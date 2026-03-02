# Upload All Logs Command

**IMPORTANT: Respond to the user in Japanese (日本語で応答してください).**

Commit current changes and upload all conversation logs to S3 using latest mode (first commit to HEAD).

First, check git status:

```bash
git status
```

If there are uncommitted changes:
1. Show the user what files have changed
2. **Ask the user: "変更をコミットしてログをアップロードしますか？ (y/n)"**
3. If the user says yes (y), ask for a commit message and commit the changes with the standard format
4. If the user says no (n), stop and do not proceed with the upload

After committing (if user confirmed), run the enhanced uploader to upload all logs:

```bash
python3 .claude/astemo_utils/enhanced_uploader.py --mode=latest
```

This will:
1. Commit current changes to git
2. Load configuration (S3 settings, project name, repo path) from .claude/uploader_config.json
3. Find all conversations from first commit to HEAD
4. Upload them to S3
5. Save upload history for future incremental uploads

Note: The command reads project name and repository path from .claude/uploader_config.json in the project directory.
If the config file is not set up, the command will fail with an error.

Report the git commit details and upload summary to the user.
