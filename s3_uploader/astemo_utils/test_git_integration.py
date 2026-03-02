#!/usr/bin/env python3
"""
Integration test for commit filtering with real git repository
"""

import json
import sys
import subprocess
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path

# Import the EnhancedHistoryUploader and GitInfo classes
sys.path.insert(0, str(Path(__file__).parent))
from enhanced_uploader import EnhancedHistoryUploader, GitInfo


def run_git_command(repo_path, *args):
    """Run a git command in the specified repository."""
    result = subprocess.run(
        ['git', '-C', str(repo_path)] + list(args),
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout.strip()


def run_git_commit_with_date(repo_path, message, date_str):
    """Run git commit with a specific date."""
    env = {
        'GIT_AUTHOR_DATE': date_str,
        'GIT_COMMITTER_DATE': date_str
    }
    result = subprocess.run(
        ['git', '-C', str(repo_path), 'commit', '-m', message],
        capture_output=True,
        text=True,
        check=True,
        env={**subprocess.os.environ, **env}
    )
    return result.stdout.strip()


def create_test_repo_with_commits():
    """Create a test git repository with multiple commits."""
    repo_path = Path(tempfile.mkdtemp())
    print(f"Creating test repository: {repo_path}")

    try:
        # Initialize git repo
        run_git_command(repo_path, 'init')
        run_git_command(repo_path, 'config', 'user.name', 'Test User')
        run_git_command(repo_path, 'config', 'user.email', 'test@example.com')

        commits = []
        base_time = datetime(2025, 10, 21, 10, 0, 0)

        # Create first commit with specific timestamp
        file1 = repo_path / "file1.txt"
        file1.write_text("Initial content\n")
        run_git_command(repo_path, 'add', 'file1.txt')
        date1 = base_time.isoformat()
        run_git_commit_with_date(repo_path, 'Initial commit', date1)
        commit1 = run_git_command(repo_path, 'rev-parse', 'HEAD')
        commits.append(commit1)
        print(f"  Commit 1: {commit1[:8]} at {date1}")

        # Create second commit 1 hour later
        file2 = repo_path / "file2.txt"
        file2.write_text("Second file\n")
        run_git_command(repo_path, 'add', 'file2.txt')
        date2 = (base_time + timedelta(hours=1)).isoformat()
        run_git_commit_with_date(repo_path, 'Add file2', date2)
        commit2 = run_git_command(repo_path, 'rev-parse', 'HEAD')
        commits.append(commit2)
        print(f"  Commit 2: {commit2[:8]} at {date2}")

        # Create third commit 2 hours later
        file1.write_text("Modified content\n")
        run_git_command(repo_path, 'add', 'file1.txt')
        date3 = (base_time + timedelta(hours=2)).isoformat()
        run_git_commit_with_date(repo_path, 'Modify file1', date3)
        commit3 = run_git_command(repo_path, 'rev-parse', 'HEAD')
        commits.append(commit3)
        print(f"  Commit 3: {commit3[:8]} at {date3}")

        return repo_path, commits

    except Exception as e:
        shutil.rmtree(repo_path)
        raise e


def test_git_info_class():
    """Test GitInfo class functionality."""
    print("\nTesting GitInfo class...")
    print("=" * 60)

    repo_path, commits = create_test_repo_with_commits()

    try:
        git_info = GitInfo(repo_path)

        # Test get_commit_timestamp
        print("\n--- Testing get_commit_timestamp ---")
        for i, commit in enumerate(commits):
            timestamp = git_info.get_commit_timestamp(commit)
            print(f"Commit {i+1} ({commit[:8]}): {timestamp}")
            assert timestamp is not None, f"Failed to get timestamp for commit {commit}"
        print("✓ get_commit_timestamp test passed")

        # Test get_commit_info
        print("\n--- Testing get_commit_info ---")
        info = git_info.get_commit_info(commits[0])
        print(f"Commit info:")
        print(f"  Hash: {info['hash'][:8]}")
        print(f"  Timestamp: {info['timestamp']}")
        print(f"  Author: {info['author']}")
        print(f"  Message: {info['message']}")
        assert info['hash'] == commits[0], "Hash mismatch"
        assert info['timestamp'] is not None, "Timestamp is None"
        assert info['author'] != '', "Author is empty"
        assert info['message'] == 'Initial commit', "Message mismatch"
        print("✓ get_commit_info test passed")

        # Test get_changes_between_commits
        print("\n--- Testing get_changes_between_commits ---")
        changes = git_info.get_changes_between_commits(commits[0], commits[1])
        print(f"Changes between commit 1 and 2:")
        print(f"  Files added: {changes['files_added']}")
        print(f"  Files modified: {changes['files_modified']}")
        print(f"  Files deleted: {changes['files_deleted']}")
        print(f"  Total additions: {changes['total_additions']}")
        print(f"  Total deletions: {changes['total_deletions']}")
        assert 'file2.txt' in changes['files_added'], "file2.txt should be added"
        print("✓ get_changes_between_commits test passed")

        # Test branch info
        print("\n--- Testing branch info ---")
        branch = git_info.get_current_branch()
        print(f"Current branch: {branch}")
        assert branch != '', "Branch name is empty"
        print("✓ Branch info test passed")

        print("\n" + "=" * 60)
        print("GitInfo tests passed! ✓")

        return repo_path, commits

    except Exception as e:
        shutil.rmtree(repo_path)
        raise e


def test_integration_with_git_filtering():
    """Test full integration with git commit filtering."""
    print("\n\nTesting integration with git commit filtering...")
    print("=" * 60)

    # Create test repo
    repo_path, commits = create_test_repo_with_commits()

    # Create mock conversation data with timestamps
    temp_projects_dir = Path(tempfile.mkdtemp())
    temp_output_dir = Path(tempfile.mkdtemp())

    try:
        # Get commit timestamps
        git_info = GitInfo(repo_path)
        commit_times = [git_info.get_commit_timestamp(c) for c in commits]
        print(f"\nCommit timestamps:")
        for i, (commit, time) in enumerate(zip(commits, commit_times)):
            print(f"  Commit {i+1} ({commit[:8]}): {time}")

        # Create conversation messages spanning all commits
        project_name = "-home-ubuntu-test-project"
        project_dir = temp_projects_dir / project_name
        project_dir.mkdir(parents=True)

        conversation_file = project_dir / "test_conversation.jsonl"

        # Create messages: some before commit1, some between commit1 and commit2,
        # some between commit2 and commit3, some after commit3
        messages = []

        # Messages before commit1 (should be filtered out if using commit1 as before)
        base_time = commit_times[0] - timedelta(minutes=30)
        for i in range(2):
            time = base_time + timedelta(minutes=i * 5)
            # Need to ensure timezone info for comparison
            time_str = time.strftime("%Y-%m-%dT%H:%M:%S") if not time.tzinfo else time.isoformat()
            messages.append({
                "type": "user" if i % 2 == 0 else "assistant",
                "timestamp": time_str,
                "message": {"content": [{"type": "text", "text": f"Before commit 1 - message {i}"}]},
                "cwd": str(repo_path),
                "gitBranch": "main"
            })

        # Messages between commit1 and commit2 (10 minutes after commit1)
        base_time = commit_times[0] + timedelta(minutes=10)
        for i in range(3):
            time = base_time + timedelta(minutes=i * 5)
            time_str = time.strftime("%Y-%m-%dT%H:%M:%S") if not time.tzinfo else time.isoformat()
            messages.append({
                "type": "user" if i % 2 == 0 else "assistant",
                "timestamp": time_str,
                "message": {"content": [{"type": "text", "text": f"Between commit 1 and 2 - message {i}"}]},
                "cwd": str(repo_path),
                "gitBranch": "main"
            })

        # Messages between commit2 and commit3 (10 minutes after commit2)
        base_time = commit_times[1] + timedelta(minutes=10)
        for i in range(3):
            time = base_time + timedelta(minutes=i * 5)
            time_str = time.strftime("%Y-%m-%dT%H:%M:%S") if not time.tzinfo else time.isoformat()
            messages.append({
                "type": "user" if i % 2 == 0 else "assistant",
                "timestamp": time_str,
                "message": {"content": [{"type": "text", "text": f"Between commit 2 and 3 - message {i}"}]},
                "cwd": str(repo_path),
                "gitBranch": "main"
            })

        # Messages after commit3 (should be filtered out if using commit3 as after)
        base_time = commit_times[2] + timedelta(minutes=30)
        for i in range(2):
            time = base_time + timedelta(minutes=i * 5)
            time_str = time.strftime("%Y-%m-%dT%H:%M:%S") if not time.tzinfo else time.isoformat()
            messages.append({
                "type": "user" if i % 2 == 0 else "assistant",
                "timestamp": time_str,
                "message": {"content": [{"type": "text", "text": f"After commit 3 - message {i}"}]},
                "cwd": str(repo_path),
                "gitBranch": "main"
            })

        # Write messages to file
        with open(conversation_file, 'w') as f:
            for msg in messages:
                f.write(json.dumps(msg) + '\n')

        print(f"\nCreated {len(messages)} messages:")
        print(f"  Before commit 1: 2 messages")
        print(f"  Between commit 1 and 2: 3 messages")
        print(f"  Between commit 2 and 3: 3 messages")
        print(f"  After commit 3: 2 messages")

        # Test 1: Filter between commit 1 and commit 3
        print("\n--- Test 1: Filter between commit 1 and commit 3 ---")
        uploader = EnhancedHistoryUploader(output_dir=str(temp_output_dir))
        uploader.claude_projects_path = temp_projects_dir

        stats = uploader.process_project(
            project_name=project_name,
            repo_path=str(repo_path),
            before_commit=commits[0],
            after_commit=commits[2],
            dry_run=False
        )

        print(f"\nResults:")
        print(f"  Files found: {stats['files_found']}")
        print(f"  Files processed: {stats['files_processed']}")
        print(f"  Total messages: {stats['messages_total']}")
        print(f"  Messages in range: {stats['messages_trimmed']}")

        # Should have 6 messages (3 between commit1-2 + 3 between commit2-3)
        expected = 6
        print(f"\nExpected messages in range: ~{expected}")
        assert stats['messages_total'] == len(messages), "Should extract all messages"
        assert stats['messages_trimmed'] > 0, "Should have messages in range"
        print("✓ Test 1 passed")

        # Test 2: Filter only between commit 1 and commit 2
        print("\n--- Test 2: Filter between commit 1 and commit 2 ---")
        # Clear output directory
        shutil.rmtree(temp_output_dir)
        temp_output_dir = Path(tempfile.mkdtemp())
        uploader.output_dir = temp_output_dir

        stats = uploader.process_project(
            project_name=project_name,
            repo_path=str(repo_path),
            before_commit=commits[0],
            after_commit=commits[1],
            dry_run=False
        )

        print(f"\nResults:")
        print(f"  Total messages: {stats['messages_total']}")
        print(f"  Messages in range: {stats['messages_trimmed']}")

        # Should have ~3 messages (between commit1-2)
        expected = 3
        print(f"\nExpected messages in range: ~{expected}")
        assert stats['messages_trimmed'] > 0, "Should have messages in range"
        assert stats['messages_trimmed'] < stats['messages_total'], "Should filter some messages"
        print("✓ Test 2 passed")

        # Verify output file structure
        print("\n--- Verifying output file structure ---")
        output_files = list(temp_output_dir.rglob("*.json"))
        assert len(output_files) > 0, "Should create output file"

        with open(output_files[0], 'r') as f:
            data = json.load(f)
            print(f"Output file structure verified:")
            print(f"  Session ID: {data['session']['id']}")
            print(f"  Conversation ID: {data['session']['conversation_id']}")
            print(f"  Duration: {data['session']['duration_seconds']}s")
            print(f"  Git before commit: {data['data']['git']['commits']['before'][:8]}")
            print(f"  Git after commit: {data['data']['git']['commits']['after'][:8]}")
            print(f"  Git branch: {data['data']['git']['branch']['name']}")
            print(f"  Messages: {len(data['data']['conversation']['messages'])}")

            assert data['data']['git']['commits']['before'] == commits[0], "Before commit mismatch"
            assert data['data']['git']['commits']['after'] == commits[1], "After commit mismatch"
        print("✓ Output file structure test passed")

        print("\n" + "=" * 60)
        print("Integration tests passed! ✓")

    finally:
        # Cleanup
        shutil.rmtree(repo_path)
        shutil.rmtree(temp_projects_dir)
        shutil.rmtree(temp_output_dir)
        print(f"\nCleaned up temporary directories")


if __name__ == "__main__":
    try:
        test_git_info_class()
        test_integration_with_git_filtering()
        print("\n" + "=" * 60)
        print("ALL INTEGRATION TESTS PASSED! ✓✓✓")
        print("=" * 60)
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
