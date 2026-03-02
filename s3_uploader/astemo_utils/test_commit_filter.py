#!/usr/bin/env python3
"""
Test script for commit filtering functionality in enhanced_uploader.py
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import shutil

# Import the EnhancedHistoryUploader class
sys.path.insert(0, str(Path(__file__).parent))
from enhanced_uploader import EnhancedHistoryUploader


def create_test_messages(base_time: datetime, count: int = 5) -> list:
    """Create test conversation messages with timestamps."""
    messages = []

    for i in range(count):
        timestamp = base_time + timedelta(minutes=i * 10)
        messages.append({
            "type": "user" if i % 2 == 0 else "assistant",
            "timestamp": timestamp.isoformat(),
            "message": {
                "content": [
                    {
                        "type": "text",
                        "text": f"Test message {i}"
                    }
                ]
            },
            "cwd": "/home/ubuntu/agents-templete",
            "gitBranch": "main"
        })

    return messages


def test_trim_conversation_by_commits():
    """Test the trim_conversation_by_commits method."""
    print("Testing trim_conversation_by_commits method...")
    print("=" * 60)

    uploader = EnhancedHistoryUploader(output_dir="/tmp/test_output")

    # Create test messages spanning 50 minutes
    base_time = datetime(2025, 10, 21, 10, 0, 0)
    messages = create_test_messages(base_time, count=6)

    print(f"\nOriginal messages: {len(messages)}")
    for i, msg in enumerate(messages):
        print(f"  Message {i}: {msg['timestamp']}")

    # Test 1: Filter by both before and after timestamps (both required)
    print("\n--- Test 1: Filter by both before and after timestamps ---")
    before_time = base_time + timedelta(minutes=10)
    after_time = base_time + timedelta(minutes=40)
    print(f"Before timestamp: {before_time.isoformat()}")
    print(f"After timestamp: {after_time.isoformat()}")
    trimmed = uploader.trim_conversation_by_commits(messages, before_time, after_time)
    print(f"Result: {len(trimmed)} messages")
    print(f"Filtered messages:")
    for msg in trimmed:
        print(f"  {msg['timestamp']}")

    # Verify all messages are within range
    for msg in trimmed:
        msg_time = datetime.fromisoformat(msg['timestamp'])
        assert msg_time >= before_time, f"Message {msg['timestamp']} is before {before_time}"
        assert msg_time <= after_time, f"Message {msg['timestamp']} is after {after_time}"
    print("✓ Test 1 passed")

    # Test 2: No messages in range
    print("\n--- Test 2: No messages in range ---")
    before_time = base_time + timedelta(hours=10)
    after_time = base_time + timedelta(hours=11)
    print(f"Before timestamp: {before_time.isoformat()}")
    print(f"After timestamp: {after_time.isoformat()}")
    trimmed = uploader.trim_conversation_by_commits(messages, before_time, after_time)
    print(f"Result: {len(trimmed)} messages (expected: 0)")
    assert len(trimmed) == 0, "Test 2 failed: Should return no messages"
    print("✓ Test 2 passed")

    print("\n" + "=" * 60)
    print("All tests passed! ✓")


def test_with_mock_project():
    """Test with a mock project and conversation file."""
    print("\n\nTesting with mock project data...")
    print("=" * 60)

    # Create temporary directories
    temp_projects_dir = Path(tempfile.mkdtemp())
    temp_output_dir = Path(tempfile.mkdtemp())

    try:
        # Create mock project structure
        project_name = "-home-ubuntu-test-project"
        project_dir = temp_projects_dir / project_name
        project_dir.mkdir(parents=True)

        # Create mock conversation file
        conversation_file = project_dir / "test_conversation.jsonl"
        base_time = datetime(2025, 10, 21, 10, 0, 0)
        messages = create_test_messages(base_time, count=10)

        with open(conversation_file, 'w') as f:
            for msg in messages:
                f.write(json.dumps(msg) + '\n')

        print(f"Created mock project: {project_dir}")
        print(f"Created mock conversation: {conversation_file}")
        print(f"Total messages: {len(messages)}")

        # Create uploader with custom projects path
        uploader = EnhancedHistoryUploader(output_dir=str(temp_output_dir))
        uploader.claude_projects_path = temp_projects_dir

        # Test processing without commit filtering
        print("\n--- Processing without commit filtering ---")
        stats = uploader.process_project(
            project_name=project_name,
            repo_path=None,
            before_commit=None,
            after_commit=None,
            dry_run=False
        )

        print(f"\nResults:")
        print(f"  Files found: {stats['files_found']}")
        print(f"  Files processed: {stats['files_processed']}")
        print(f"  Files saved: {stats['files_saved']}")
        print(f"  Total messages: {stats['messages_total']}")
        print(f"  Messages in range: {stats['messages_trimmed']}")

        assert stats['files_found'] == 1, "Should find 1 conversation file"
        assert stats['files_processed'] == 1, "Should process 1 file"
        assert stats['files_saved'] == 1, "Should save 1 file"
        assert stats['messages_total'] == len(messages), f"Should extract {len(messages)} messages"

        # Check output file was created
        output_files = list(temp_output_dir.rglob("*.json"))
        print(f"\nOutput files created: {len(output_files)}")
        for f in output_files:
            print(f"  {f}")

            # Read and verify the output
            with open(f, 'r') as file:
                data = json.load(file)
                print(f"\nOutput file structure:")
                print(f"  Session ID: {data['session']['id']}")
                print(f"  Total turns: {data['data']['conversation']['total_turns']}")
                print(f"  Total tokens: {data['data']['conversation']['total_tokens']}")
                print(f"  Project name: {data['metadata']['project']['name']}")

        print("\n✓ Mock project test passed")

    finally:
        # Cleanup
        shutil.rmtree(temp_projects_dir)
        shutil.rmtree(temp_output_dir)
        print(f"\nCleaned up temporary directories")


if __name__ == "__main__":
    try:
        test_trim_conversation_by_commits()
        # Note: test_with_mock_project removed because enhanced_uploader now requires
        # commit parameters. See test_git_integration.py for full integration tests.
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED! ✓✓✓")
        print("=" * 60)
        print("\nNote: Run test_git_integration.py for full integration tests with git.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
