# Upload Logs Command

**IMPORTANT: Respond to the user in Japanese (日本語で応答してください).**

Commit current changes and upload conversation logs to S3 using incremental mode.

First, check git status:

```bash
git status
```

If there are uncommitted changes:
1. Show the user what files have changed
2. **Ask the user: "変更をコミットしてログをアップロードしますか？ (y/n)"**
3. If the user says yes (y), ask for a commit message and commit the changes with the standard format
4. If the user says no (n), stop and do not proceed with the upload

After committing (if user confirmed), run the enhanced uploader to upload logs from the last uploaded commit to HEAD:

```bash
python3 .claude/astemo_utils/enhanced_uploader.py --mode=incremental
```

This will:
1. Commit current changes to git
2. Load configuration (S3 settings, project name, repo path) from .claude/uploader_config.json
3. Find conversations since the last upload
4. Upload them to S3
5. Update upload history

Note: The command reads project name and repository path from .claude/uploader_config.json in the project directory.
If the config file is not set up, the command will fail with an error.

Report the git commit details and upload summary to the user.
