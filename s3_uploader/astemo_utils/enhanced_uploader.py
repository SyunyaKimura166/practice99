#!/usr/bin/env python3
"""
Enhanced Claude Code Conversation History Uploader with Git Integration

This script extracts conversation history from ~/.claude/projects,
correlates them with git commits, and uploads structured data.
"""

import json
import os
import sys
import subprocess
import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False


class GitInfo:
    """Git repository information extractor."""

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)

    def run_git_command(self, *args) -> str:
        """Run a git command and return output."""
        try:
            result = subprocess.run(
                ['git', '-C', str(self.repo_path)] + list(args),
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Git command failed: {e.stderr}")
            return ""

    def get_commit_timestamp(self, commit_hash: str) -> Optional[datetime]:
        """Get timestamp of a commit."""
        if not commit_hash:
            return None

        timestamp_str = self.run_git_command('show', '-s', '--format=%cI', commit_hash)
        if timestamp_str:
            try:
                return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except ValueError:
                return None
        return None

    def get_commit_info(self, commit_hash: str) -> Dict[str, Any]:
        """Get detailed information about a commit."""
        if not commit_hash:
            return {}

        info = {
            'hash': commit_hash,
            'timestamp': None,
            'author': '',
            'message': ''
        }

        # Get timestamp
        timestamp = self.get_commit_timestamp(commit_hash)
        if timestamp:
            info['timestamp'] = timestamp.isoformat()

        # Get author
        author = self.run_git_command('show', '-s', '--format=%an <%ae>', commit_hash)
        if author:
            info['author'] = author

        # Get commit message
        message = self.run_git_command('show', '-s', '--format=%B', commit_hash)
        if message:
            info['message'] = message.strip()

        return info

    def get_changes_between_commits(self, before: str, after: str) -> Dict[str, Any]:
        """Get file changes between two commits."""
        changes = {
            'files_added': [],
            'files_modified': [],
            'files_deleted': [],
            'total_additions': 0,
            'total_deletions': 0
        }

        if not before or not after:
            return changes

        # Get file status changes
        diff_output = self.run_git_command('diff', '--name-status', f'{before}..{after}')
        for line in diff_output.split('\n'):
            if not line:
                continue
            parts = line.split('\t', 1)
            if len(parts) != 2:
                continue
            status, filename = parts

            if status == 'A':
                changes['files_added'].append(filename)
            elif status == 'M':
                changes['files_modified'].append(filename)
            elif status == 'D':
                changes['files_deleted'].append(filename)

        # Get addition/deletion stats
        stat_output = self.run_git_command('diff', '--numstat', f'{before}..{after}')
        for line in stat_output.split('\n'):
            if not line:
                continue
            parts = line.split('\t')
            if len(parts) >= 2:
                try:
                    additions = int(parts[0]) if parts[0] != '-' else 0
                    deletions = int(parts[1]) if parts[1] != '-' else 0
                    changes['total_additions'] += additions
                    changes['total_deletions'] += deletions
                except ValueError:
                    continue

        return changes

    def get_current_branch(self) -> str:
        """Get current branch name."""
        return self.run_git_command('rev-parse', '--abbrev-ref', 'HEAD')

    def get_remote_url(self) -> str:
        """Get remote repository URL."""
        return self.run_git_command('config', '--get', 'remote.origin.url')

    def get_first_commit(self) -> str:
        """Get the first commit in the repository."""
        return self.run_git_command('rev-list', '--max-parents=0', 'HEAD')

    def get_previous_commit(self, commit: str = 'HEAD') -> str:
        """Get the previous commit (commit~1)."""
        return self.run_git_command('rev-parse', f'{commit}~1')


class EnhancedHistoryUploader:
    @staticmethod
    def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Load configuration from JSON file.

        Args:
            config_path: Path to config file (defaults to .claude/uploader_config.json in current directory)

        Returns:
            Configuration dictionary
        """
        if config_path is None:
            config_path = Path(".claude") / "uploader_config.json"

        if not config_path.exists():
            return {}

        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            return config
        except Exception as e:
            print(f"Warning: Failed to load config from {config_path}: {e}")
            return {}

    def __init__(self, s3_bucket: Optional[str] = None, s3_prefix: str = "claude_history",
                 output_dir: Optional[str] = None, config_path: Optional[Path] = None):
        """
        Initialize the enhanced uploader.

        Args:
            s3_bucket: S3 bucket name (optional, required for S3 upload)
            s3_prefix: Prefix for S3 keys (default: "claude_history")
            output_dir: Local directory for file output (optional, required for file output)
            config_path: Path to config file (optional, defaults to ~/.claude/uploader_config.json)
        """
        # Load config file
        config = self.load_config(config_path)

        # Use config values if command-line arguments not provided
        if s3_bucket is None and 's3' in config:
            s3_bucket = config['s3'].get('bucket')
        if s3_prefix == "claude_history" and 's3' in config:
            s3_prefix = config['s3'].get('prefix', s3_prefix)

        self.claude_projects_path = Path.home() / ".claude" / "projects"
        self.upload_history_path = Path.home() / ".claude" / "upload_history"
        self.s3_bucket = s3_bucket
        self.s3_prefix = s3_prefix
        self.output_dir = Path(output_dir) if output_dir else None

        # Create upload history directory if it doesn't exist
        self.upload_history_path.mkdir(parents=True, exist_ok=True)

        # Initialize S3 client only if bucket is specified
        if s3_bucket:
            if not BOTO3_AVAILABLE:
                raise ImportError("boto3 is required for S3 upload. Install it with: pip install boto3")
            self.s3_client = boto3.client('s3')
        else:
            self.s3_client = None

    def get_upload_history_file(self, project_name: str) -> Path:
        """Get the upload history file path for a project."""
        return self.upload_history_path / f"{project_name}.json"

    def load_upload_history(self, project_name: str) -> Optional[Dict[str, Any]]:
        """Load upload history for a project."""
        history_file = self.get_upload_history_file(project_name)
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load upload history: {e}")
        return None

    def save_upload_history(self, project_name: str, commit_hash: str, repo_path: str):
        """Save upload history for a project."""
        history_file = self.get_upload_history_file(project_name)
        history = {
            'project_name': project_name,
            'last_uploaded_commit': commit_hash,
            'last_uploaded_at': datetime.now().isoformat(),
            'repo_path': repo_path
        }
        try:
            with open(history_file, 'w') as f:
                json.dump(history, f, indent=2)
            print(f"Saved upload history: {commit_hash}")
        except Exception as e:
            print(f"Warning: Failed to save upload history: {e}")

    def find_conversation_files(self) -> List[Tuple[str, Path]]:
        """Find all conversation history files in ~/.claude/projects."""
        conversation_files = []

        if not self.claude_projects_path.exists():
            print(f"Warning: {self.claude_projects_path} does not exist")
            return conversation_files

        for project_dir in self.claude_projects_path.iterdir():
            if project_dir.is_dir():
                project_name = project_dir.name
                for jsonl_file in project_dir.glob("*.jsonl"):
                    conversation_files.append((project_name, jsonl_file))

        return conversation_files

    def extract_conversation(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract conversation data from a JSONL file."""
        messages = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            data = json.loads(line)
                            messages.append(data)
                        except json.JSONDecodeError as e:
                            print(f"Warning: Failed to parse line in {file_path}: {e}")
                            continue
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")

        return messages

    def trim_conversation_by_commits(self, messages: List[Dict[str, Any]],
                                     before_timestamp: Optional[datetime],
                                     after_timestamp: Optional[datetime]) -> List[Dict[str, Any]]:
        """
        Trim conversation messages to only include those between before and after commit timestamps.

        Args:
            messages: List of conversation messages
            before_timestamp: Start timestamp (commit before) - REQUIRED
            after_timestamp: End timestamp (commit after) - REQUIRED

        Returns:
            Filtered list of messages within the commit range
        """
        if not before_timestamp or not after_timestamp:
            raise ValueError("Both before_timestamp and after_timestamp are required for commit filtering")

        trimmed = []

        for msg in messages:
            # Check if message has a timestamp
            msg_timestamp_str = msg.get('timestamp')
            if not msg_timestamp_str:
                continue

            try:
                msg_timestamp = datetime.fromisoformat(msg_timestamp_str.replace('Z', '+00:00'))
            except ValueError:
                continue

            # Filter by timestamp range: before_timestamp <= msg_timestamp <= after_timestamp
            if msg_timestamp < before_timestamp:
                continue
            if msg_timestamp > after_timestamp:
                continue

            trimmed.append(msg)

        return trimmed

    def extract_io_summary(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract input/output summary from conversation messages."""
        summary = {
            'user_requests': [],
            'agent_actions': {
                'tool_uses': [],
                'files_read': [],
                'files_written': [],
                'commands_executed': []
            },
            'outcomes': {
                'completed_tasks': [],
                'failed_tasks': [],
                'errors': []
            }
        }

        for msg in messages:
            msg_type = msg.get('type')
            message_data = msg.get('message', {})

            # Extract user messages
            if msg_type == 'user':
                content = message_data.get('content', [])
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get('type') == 'text':
                            summary['user_requests'].append({
                                'timestamp': msg.get('timestamp'),
                                'text': item.get('text', '')[:200]  # Truncate long messages
                            })

            # Extract assistant actions
            elif msg_type == 'assistant':
                content = message_data.get('content', [])
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict):
                            item_type = item.get('type')
                            if item_type == 'tool_use':
                                summary['agent_actions']['tool_uses'].append({
                                    'timestamp': msg.get('timestamp'),
                                    'tool': item.get('name'),
                                    'id': item.get('id')
                                })

        return summary

    def calculate_token_stats(self, messages: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate total token usage from messages."""
        stats = {
            'input': 0,
            'output': 0,
            'total': 0
        }

        for msg in messages:
            message_data = msg.get('message', {})
            usage = message_data.get('usage', {})

            stats['input'] += usage.get('input_tokens', 0)
            stats['output'] += usage.get('output_tokens', 0)

        stats['total'] = stats['input'] + stats['output']
        return stats

    def create_enhanced_schema(self, project_name: str, conversation_id: str,
                              messages: List[Dict[str, Any]], repo_path: Optional[str],
                              before_commit: Optional[str], after_commit: Optional[str]) -> Dict[str, Any]:
        """
        Create data in the enhanced schema format.

        Args:
            project_name: Name of the project
            conversation_id: Conversation ID
            messages: List of conversation messages
            repo_path: Path to the git repository
            before_commit: Commit hash before the session
            after_commit: Commit hash after the session

        Returns:
            Dictionary with enhanced schema
        """
        # Get session timing
        session_start = None
        session_end = None

        for msg in messages:
            ts = msg.get('timestamp')
            if ts:
                try:
                    dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    if not session_start or dt < session_start:
                        session_start = dt
                    if not session_end or dt > session_end:
                        session_end = dt
                except ValueError:
                    pass

        # Calculate duration
        duration_seconds = 0
        if session_start and session_end:
            duration_seconds = int((session_end - session_start).total_seconds())

        # Get git information
        git_data = {
            'commits': {
                'before': before_commit or '',
                'after': after_commit or ''
            },
            'branch': {
                'name': '',
                'base': ''
            },
            'changes': {
                'files_added': [],
                'files_modified': [],
                'files_deleted': [],
                'total_additions': 0,
                'total_deletions': 0
            }
        }

        if repo_path:
            git_info = GitInfo(repo_path)
            git_data['branch']['name'] = git_info.get_current_branch()

            if before_commit and after_commit:
                git_data['changes'] = git_info.get_changes_between_commits(before_commit, after_commit)

        # Extract first cwd and gitBranch from messages
        cwd = None
        git_branch = None
        for msg in messages:
            if not cwd and 'cwd' in msg:
                cwd = msg['cwd']
            if not git_branch and 'gitBranch' in msg:
                git_branch = msg['gitBranch']
            if cwd and git_branch:
                break

        if git_branch:
            git_data['branch']['name'] = git_branch

        # Get repo URL if available
        repo_url = ''
        if repo_path:
            git_info = GitInfo(repo_path)
            repo_url = git_info.get_remote_url()

        # Create enhanced schema
        schema = {
            'session': {
                'id': str(uuid.uuid4()),
                'conversation_id': conversation_id,
                'started_at': session_start.isoformat() if session_start else '',
                'ended_at': session_end.isoformat() if session_end else '',
                'duration_seconds': duration_seconds
            },
            'data': {
                'conversation': {
                    'messages': messages,
                    'total_turns': len(messages),
                    'total_tokens': self.calculate_token_stats(messages)
                },
                'git': git_data,
                'io_summary': self.extract_io_summary(messages)
            },
            'metadata': {
                'project': {
                    'name': project_name,
                    'repo_url': repo_url,
                    'local_path': cwd or ''
                },
                'user': {
                    'id': os.environ.get('USER', ''),
                    'email': ''
                },
                'agent': {
                    'name': 'claude-code',
                    'model': '',
                    'version': ''
                },
                'environment': {
                    'os': os.uname().sysname if hasattr(os, 'uname') else 'unknown',
                    'platform': sys.platform,
                    'working_directory': cwd or ''
                },
                'feedback': {
                    'rating': None,
                    'comment': '',
                    'submitted_at': ''
                }
            }
        }

        # Extract agent info and count model usage
        model_usage = {}
        agent_version = ''

        for msg in messages:
            # Count model usage
            model = None
            message_data = msg.get('message', {})

            # Try to get model from message.model
            if 'model' in message_data:
                model = message_data['model']
            # Try to get model from top-level model field
            elif 'model' in msg:
                model = msg['model']

            if model:
                model_usage[model] = model_usage.get(model, 0) + 1

            # Get version (only need to find once)
            if not agent_version and 'version' in msg:
                agent_version = msg['version']

        # Set the most used model as the primary model
        if model_usage:
            most_used_model = max(model_usage.items(), key=lambda x: x[1])[0]
            schema['metadata']['agent']['model'] = most_used_model
            schema['metadata']['agent']['model_usage'] = model_usage

        if agent_version:
            schema['metadata']['agent']['version'] = agent_version

        return schema

    def upload_to_s3(self, data: Dict[str, Any], s3_key: str) -> bool:
        """Upload data to S3."""
        try:
            json_data = json.dumps(data, ensure_ascii=False, indent=2)

            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=s3_key,
                Body=json_data.encode('utf-8'),
                ContentType='application/json',
                Metadata={
                    'uploaded_at': datetime.now().isoformat(),
                    'source': 'claude_code_history_enhanced'
                }
            )

            print(f"Successfully uploaded to s3://{self.s3_bucket}/{s3_key}")
            return True

        except ClientError as e:
            print(f"Error uploading to S3: {e}")
            return False

    def save_to_file(self, data: Dict[str, Any], file_path: Path) -> bool:
        """Save data to a local file."""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            json_data = json.dumps(data, ensure_ascii=False, indent=2)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(json_data)

            print(f"Successfully saved to {file_path}")
            return True

        except Exception as e:
            print(f"Error saving to file: {e}")
            return False

    def process_project(self, project_name: str, repo_path: Optional[str] = None,
                       before_commit: Optional[str] = None, after_commit: Optional[str] = None,
                       dry_run: bool = False) -> Dict[str, int]:
        """
        Process conversations from a project with optional commit filtering.

        Args:
            project_name: Name of the project directory
            repo_path: Path to git repository (for git info extraction)
            before_commit: Start commit hash (conversations after this commit)
            after_commit: End commit hash (conversations before this commit)
            dry_run: If True, don't actually upload/save

        Returns:
            Dictionary with statistics
        """
        stats = {
            'files_found': 0,
            'files_processed': 0,
            'files_saved': 0,
            'messages_total': 0,
            'messages_trimmed': 0
        }

        project_path = self.claude_projects_path / project_name

        if not project_path.exists():
            print(f"Error: Project directory {project_path} does not exist")
            return stats

        conversation_files = list(project_path.glob("*.jsonl"))
        stats['files_found'] = len(conversation_files)

        print(f"Found {stats['files_found']} conversation files in {project_name}")

        # Get commit timestamps for filtering
        before_timestamp = None
        after_timestamp = None

        if repo_path:
            git_info = GitInfo(repo_path)
            if before_commit:
                before_timestamp = git_info.get_commit_timestamp(before_commit)
                print(f"Before commit: {before_commit} ({before_timestamp})")
            if after_commit:
                after_timestamp = git_info.get_commit_timestamp(after_commit)
                print(f"After commit: {after_commit} ({after_timestamp})")

        for file_path in conversation_files:
            print(f"\nProcessing: {file_path.name}")

            messages = self.extract_conversation(file_path)
            stats['messages_total'] += len(messages)

            if not messages:
                print(f"  No messages found")
                continue

            print(f"  Extracted {len(messages)} messages")

            # Trim by commit timestamps
            trimmed_messages = self.trim_conversation_by_commits(
                messages, before_timestamp, after_timestamp
            )

            stats['messages_trimmed'] += len(trimmed_messages)

            if not trimmed_messages:
                print(f"  No messages in commit range")
                continue

            print(f"  Trimmed to {len(trimmed_messages)} messages in commit range")

            stats['files_processed'] += 1

            # Create enhanced schema
            conversation_id = file_path.stem
            enhanced_data = self.create_enhanced_schema(
                project_name, conversation_id, trimmed_messages,
                repo_path, before_commit, after_commit
            )

            # Save or upload
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            if dry_run:
                if self.s3_bucket:
                    s3_key = f"{self.s3_prefix}/{project_name}/{after_commit}/{conversation_id}_{timestamp}.json"
                    print(f"  [DRY RUN] Would upload to: s3://{self.s3_bucket}/{s3_key}")
                elif self.output_dir:
                    output_file = self.output_dir / project_name / after_commit / f"{conversation_id}_{timestamp}.json"
                    print(f"  [DRY RUN] Would save to: {output_file}")
            else:
                success = False
                if self.s3_bucket:
                    s3_key = f"{self.s3_prefix}/{project_name}/{after_commit}/{conversation_id}_{timestamp}.json"
                    success = self.upload_to_s3(enhanced_data, s3_key)
                elif self.output_dir:
                    output_file = self.output_dir / project_name / after_commit / f"{conversation_id}_{timestamp}.json"
                    success = self.save_to_file(enhanced_data, output_file)

                if success:
                    stats['files_saved'] += 1

        return stats


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Extract Claude Code conversation history with git commit filtering',
        epilog='Modes: manual (default), incremental, latest'
    )
    parser.add_argument(
        '--bucket',
        help='S3 bucket name (for S3 upload)'
    )
    parser.add_argument(
        '--prefix',
        default='claude_history',
        help='S3 key prefix (default: claude_history)'
    )
    parser.add_argument(
        '--output-dir',
        help='Local directory for file output (alternative to S3 upload)'
    )
    parser.add_argument(
        '--project',
        help='Project name to process (e.g., -home-ubuntu-agents-templete). Can be specified in config file.'
    )
    parser.add_argument(
        '--repo-path',
        help='Path to git repository (required for git commit filtering). Can be specified in config file.'
    )
    parser.add_argument(
        '--mode',
        choices=['manual', 'incremental', 'latest'],
        default='manual',
        help='Upload mode: manual (specify commits), incremental (last uploaded to HEAD), latest (first to HEAD)'
    )
    parser.add_argument(
        '--before-commit',
        help='Start commit hash (required for manual mode)'
    )
    parser.add_argument(
        '--after-commit',
        help='End commit hash (required for manual mode)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Perform a dry run without uploading/saving'
    )
    parser.add_argument(
        '--config',
        help='Path to config file (default: .claude/uploader_config.json)'
    )

    args = parser.parse_args()

    # Load config to check if S3 settings are available
    config_path = Path(args.config) if args.config else None
    config = EnhancedHistoryUploader.load_config(config_path)

    # Get project name and repo path from config if not provided
    project_name = args.project
    repo_path = args.repo_path

    if 'project' in config:
        if not project_name:
            project_name = config['project'].get('name')
        if not repo_path:
            repo_path = config['project'].get('repo_path')

    # Validate arguments
    has_s3_config = 's3' in config and config['s3'].get('bucket')
    if not args.bucket and not args.output_dir and not has_s3_config:
        parser.error("Either --bucket, --output-dir, or S3 config in config file must be specified")

    if args.bucket and args.output_dir:
        parser.error("Only one of --bucket or --output-dir can be specified")

    if not project_name:
        parser.error("--project is required (either as argument or in config file)")

    if not repo_path:
        parser.error("--repo-path is required (either as argument or in config file)")

    # Validate mode-specific arguments
    if args.mode == 'manual':
        if not args.before_commit or not args.after_commit:
            parser.error("--before-commit and --after-commit are required for manual mode")

    try:
        uploader = EnhancedHistoryUploader(
            s3_bucket=args.bucket,
            s3_prefix=args.prefix,
            output_dir=args.output_dir,
            config_path=config_path
        )
    except ImportError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Determine commits based on mode
    before_commit = args.before_commit
    after_commit = args.after_commit

    if args.mode in ['incremental', 'latest']:
        git_info = GitInfo(repo_path)

        if args.mode == 'incremental':
            # Get last uploaded commit from history
            history = uploader.load_upload_history(project_name)
            if not history:
                print("Error: No upload history found. Cannot use incremental mode.")
                print("Please use manual mode or latest mode for the first upload.")
                sys.exit(1)
            before_commit = history['last_uploaded_commit']
            print(f"Last uploaded commit: {before_commit}")

            # Get HEAD (latest commit) for incremental mode
            try:
                result = subprocess.run(
                    ['git', 'rev-parse', 'HEAD'],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    check=True
                )
                after_commit = result.stdout.strip()
                print(f"Latest commit (HEAD): {after_commit}")

                # Check if there are new commits
                if before_commit == after_commit:
                    print("No new commits since last upload.")
                    sys.exit(0)
            except Exception as e:
                print(f"Error: Could not get HEAD commit: {e}")
                sys.exit(1)

        elif args.mode == 'latest':
            # Get first commit
            first_commit = git_info.get_first_commit()
            if not first_commit:
                print("Error: Could not get first commit from repository")
                sys.exit(1)
            before_commit = first_commit
            print(f"First commit: {first_commit}")

            # Get HEAD (latest commit)
            try:
                after_commit = 'HEAD'
                # Verify HEAD exists
                if not git_info.get_commit_timestamp(after_commit):
                    print("Error: Could not get HEAD commit")
                    sys.exit(1)
                # Get actual commit hash for display
                result = subprocess.run(
                    ['git', 'rev-parse', 'HEAD'],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    check=True
                )
                after_commit_hash = result.stdout.strip()
                print(f"Latest commit (HEAD): {after_commit_hash}")
                after_commit = after_commit_hash
            except Exception as e:
                print(f"Error: Could not get HEAD commit: {e}")
                sys.exit(1)

    stats = uploader.process_project(
        project_name=project_name,
        repo_path=repo_path,
        before_commit=before_commit,
        after_commit=after_commit,
        dry_run=args.dry_run
    )

    # Save upload history (only if not dry run and mode is latest)
    if not args.dry_run and args.mode == 'latest' and after_commit:
        uploader.save_upload_history(project_name, after_commit, repo_path)

    print("\n" + "="*60)
    print("Summary:")
    print(f"  Files found: {stats['files_found']}")
    print(f"  Files processed: {stats['files_processed']}")
    print(f"  Files saved: {stats['files_saved']}")
    print(f"  Total messages: {stats['messages_total']}")
    print(f"  Messages in commit range: {stats['messages_trimmed']}")
    print("="*60)


if __name__ == "__main__":
    main()
