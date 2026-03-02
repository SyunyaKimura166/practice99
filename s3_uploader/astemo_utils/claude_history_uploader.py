#!/usr/bin/env python3
"""
Claude Code Conversation History Uploader

This script extracts conversation history from ~/.claude/projects
and uploads them to AWS S3 or saves to local files.
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False


class ClaudeHistoryUploader:
    def __init__(self, s3_bucket: Optional[str] = None, s3_prefix: str = "claude_history",
                 output_dir: Optional[str] = None):
        """
        Initialize the uploader.

        Args:
            s3_bucket: S3 bucket name (optional, required for S3 upload)
            s3_prefix: Prefix for S3 keys (default: "claude_history")
            output_dir: Local directory for file output (optional, required for file output)
        """
        self.claude_projects_path = Path.home() / ".claude" / "projects"
        self.s3_bucket = s3_bucket
        self.s3_prefix = s3_prefix
        self.output_dir = Path(output_dir) if output_dir else None

        # Initialize S3 client only if bucket is specified
        if s3_bucket:
            if not BOTO3_AVAILABLE:
                raise ImportError("boto3 is required for S3 upload. Install it with: pip install boto3")
            self.s3_client = boto3.client('s3')
        else:
            self.s3_client = None

    def find_conversation_files(self) -> List[tuple]:
        """
        Find all conversation history files in ~/.claude/projects.

        Returns:
            List of tuples (project_name, file_path)
        """
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
        """
        Extract conversation data from a JSONL file.

        Args:
            file_path: Path to the JSONL file

        Returns:
            List of conversation messages
        """
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

    def upload_to_s3(self, data: Dict[str, Any], s3_key: str) -> bool:
        """
        Upload data to S3.

        Args:
            data: Dictionary containing the data to upload
            s3_key: S3 object key

        Returns:
            True if successful, False otherwise
        """
        try:
            json_data = json.dumps(data, ensure_ascii=False, indent=2)

            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=s3_key,
                Body=json_data.encode('utf-8'),
                ContentType='application/json',
                Metadata={
                    'uploaded_at': datetime.now().isoformat(),
                    'source': 'claude_code_history'
                }
            )

            print(f"Successfully uploaded to s3://{self.s3_bucket}/{s3_key}")
            return True

        except ClientError as e:
            print(f"Error uploading to S3: {e}")
            return False

    def save_to_file(self, data: Dict[str, Any], file_path: Path) -> bool:
        """
        Save data to a local file.

        Args:
            data: Dictionary containing the data to save
            file_path: Path to the output file

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)

            json_data = json.dumps(data, ensure_ascii=False, indent=2)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(json_data)

            print(f"Successfully saved to {file_path}")
            return True

        except Exception as e:
            print(f"Error saving to file: {e}")
            return False

    def process_and_upload(self, dry_run: bool = False) -> Dict[str, int]:
        """
        Process all conversation files and upload to S3 or save to files.

        Args:
            dry_run: If True, don't actually upload/save

        Returns:
            Dictionary with statistics
        """
        stats = {
            'files_found': 0,
            'files_processed': 0,
            'files_saved': 0,
            'messages_extracted': 0
        }

        conversation_files = self.find_conversation_files()
        stats['files_found'] = len(conversation_files)

        print(f"Found {stats['files_found']} conversation files")

        for project_name, file_path in conversation_files:
            print(f"\nProcessing: {project_name}/{file_path.name}")

            messages = self.extract_conversation(file_path)
            stats['messages_extracted'] += len(messages)
            stats['files_processed'] += 1

            if not messages:
                print(f"  No messages found in {file_path.name}")
                continue

            print(f"  Extracted {len(messages)} messages")

            # Prepare data
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            conversation_id = file_path.stem  # filename without extension

            upload_data = {
                'project_name': project_name,
                'conversation_id': conversation_id,
                'file_name': file_path.name,
                'extracted_at': datetime.now().isoformat(),
                'message_count': len(messages),
                'messages': messages
            }

            if dry_run:
                if self.s3_bucket:
                    s3_key = f"{self.s3_prefix}/{project_name}/{conversation_id}_{timestamp}.json"
                    print(f"  [DRY RUN] Would upload to: s3://{self.s3_bucket}/{s3_key}")
                elif self.output_dir:
                    output_file = self.output_dir / project_name / f"{conversation_id}_{timestamp}.json"
                    print(f"  [DRY RUN] Would save to: {output_file}")
            else:
                success = False
                if self.s3_bucket:
                    s3_key = f"{self.s3_prefix}/{project_name}/{conversation_id}_{timestamp}.json"
                    success = self.upload_to_s3(upload_data, s3_key)
                elif self.output_dir:
                    output_file = self.output_dir / project_name / f"{conversation_id}_{timestamp}.json"
                    success = self.save_to_file(upload_data, output_file)

                if success:
                    stats['files_saved'] += 1

        return stats

    def process_single_project(self, project_name: str, dry_run: bool = False) -> bool:
        """
        Process conversations from a single project.

        Args:
            project_name: Name of the project directory
            dry_run: If True, don't actually upload/save

        Returns:
            True if successful, False otherwise
        """
        project_path = self.claude_projects_path / project_name

        if not project_path.exists():
            print(f"Error: Project directory {project_path} does not exist")
            return False

        conversation_files = list(project_path.glob("*.jsonl"))

        if not conversation_files:
            print(f"No conversation files found in {project_name}")
            return False

        print(f"Found {len(conversation_files)} conversation files in {project_name}")

        for file_path in conversation_files:
            print(f"\nProcessing: {file_path.name}")

            messages = self.extract_conversation(file_path)

            if not messages:
                print(f"  No messages found")
                continue

            print(f"  Extracted {len(messages)} messages")

            # Prepare data
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            conversation_id = file_path.stem

            upload_data = {
                'project_name': project_name,
                'conversation_id': conversation_id,
                'file_name': file_path.name,
                'extracted_at': datetime.now().isoformat(),
                'message_count': len(messages),
                'messages': messages
            }

            if dry_run:
                if self.s3_bucket:
                    s3_key = f"{self.s3_prefix}/{project_name}/{conversation_id}_{timestamp}.json"
                    print(f"  [DRY RUN] Would upload to: s3://{self.s3_bucket}/{s3_key}")
                elif self.output_dir:
                    output_file = self.output_dir / project_name / f"{conversation_id}_{timestamp}.json"
                    print(f"  [DRY RUN] Would save to: {output_file}")
            else:
                if self.s3_bucket:
                    s3_key = f"{self.s3_prefix}/{project_name}/{conversation_id}_{timestamp}.json"
                    self.upload_to_s3(upload_data, s3_key)
                elif self.output_dir:
                    output_file = self.output_dir / project_name / f"{conversation_id}_{timestamp}.json"
                    self.save_to_file(upload_data, output_file)

        return True


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Extract Claude Code conversation history and upload to S3 or save to local files',
        epilog='Either --bucket or --output-dir must be specified.'
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
        help='Process only a specific project (e.g., -home-ubuntu-agents-templete)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Perform a dry run without uploading/saving'
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.bucket and not args.output_dir:
        parser.error("Either --bucket or --output-dir must be specified")

    if args.bucket and args.output_dir:
        parser.error("Only one of --bucket or --output-dir can be specified")

    try:
        uploader = ClaudeHistoryUploader(
            s3_bucket=args.bucket,
            s3_prefix=args.prefix,
            output_dir=args.output_dir
        )
    except ImportError as e:
        print(f"Error: {e}")
        sys.exit(1)

    if args.project:
        success = uploader.process_single_project(args.project, dry_run=args.dry_run)
        if not success:
            sys.exit(1)
    else:
        stats = uploader.process_and_upload(dry_run=args.dry_run)

        print("\n" + "="*60)
        print("Summary:")
        print(f"  Files found: {stats['files_found']}")
        print(f"  Files processed: {stats['files_processed']}")
        print(f"  Files saved: {stats['files_saved']}")
        print(f"  Total messages extracted: {stats['messages_extracted']}")
        print("="*60)


if __name__ == "__main__":
    main()
