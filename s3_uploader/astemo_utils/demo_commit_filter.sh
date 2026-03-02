#!/bin/bash
# デモンストレーション: コミットフィルタリング機能の使用例

echo "========================================"
echo "コミットフィルタリング デモ"
echo "========================================"
echo ""

# プロジェクト設定
PROJECT_NAME="-home-ubuntu-agents-templete"
REPO_PATH="/home/ubuntu/agents-templete"
OUTPUT_DIR="./tmp/filtered_output"

echo "設定:"
echo "  プロジェクト: $PROJECT_NAME"
echo "  リポジトリパス: $REPO_PATH"
echo "  出力ディレクトリ: $OUTPUT_DIR"
echo ""

# 1. 利用可能なコミットを表示
echo "--- 利用可能なコミット ---"
cd "$REPO_PATH"
if [ -d .git ]; then
    echo "最近のコミット（最新10件）:"
    git log --oneline -10 || echo "コミットがまだありません"
    echo ""

    # コミット数を確認
    COMMIT_COUNT=$(git rev-list --all --count 2>/dev/null || echo "0")

    if [ "$COMMIT_COUNT" -gt 1 ]; then
        echo "テストに使用するコミット:"
        LATEST_COMMIT=$(git rev-parse HEAD 2>/dev/null)
        PREV_COMMIT=$(git rev-parse HEAD~1 2>/dev/null)

        echo "  最新コミット: $LATEST_COMMIT"
        echo "  前のコミット: $PREV_COMMIT"
        echo ""

        # 2. ドライランでフィルタリングをテスト
        echo "--- ドライランテスト ---"
        echo "前のコミットから最新コミットまでの会話をフィルタリング..."
        python3 enhanced_uploader.py \
            --project "$PROJECT_NAME" \
            --output-dir "$OUTPUT_DIR" \
            --repo-path "$REPO_PATH" \
            --before-commit "$PREV_COMMIT" \
            --after-commit "$LATEST_COMMIT" \
            --dry-run
        echo ""

        # 3. 実際にフィルタリングを実行
        echo "--- 実際の実行 ---"
        echo "フィルタリングを実行してファイルに保存..."
        python3 enhanced_uploader.py \
            --project "$PROJECT_NAME" \
            --output-dir "$OUTPUT_DIR" \
            --repo-path "$REPO_PATH" \
            --before-commit "$PREV_COMMIT" \
            --after-commit "$LATEST_COMMIT"
        echo ""

        # 4. 結果を表示
        echo "--- 結果 ---"
        if [ -d "$OUTPUT_DIR" ]; then
            echo "生成されたファイル:"
            find "$OUTPUT_DIR" -name "*.json" -type f -exec ls -lh {} \;
            echo ""

            # 最新のJSONファイルの概要を表示
            LATEST_JSON=$(find "$OUTPUT_DIR" -name "*.json" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -f2- -d" ")
            if [ -n "$LATEST_JSON" ]; then
                echo "最新ファイルの概要: $LATEST_JSON"
                echo "---"
                python3 -c "
import json
import sys
with open('$LATEST_JSON', 'r') as f:
    data = json.load(f)
    print(f\"Session ID: {data['session']['id']}\")
    print(f\"開始時刻: {data['session']['started_at']}\")
    print(f\"終了時刻: {data['session']['ended_at']}\")
    print(f\"期間: {data['session']['duration_seconds']}秒\")
    print(f\"メッセージ数: {data['data']['conversation']['total_turns']}\")
    print(f\"Git before: {data['data']['git']['commits']['before'][:8]}\")
    print(f\"Git after: {data['data']['git']['commits']['after'][:8]}\")
    print(f\"追加ファイル数: {len(data['data']['git']['changes']['files_added'])}\")
    print(f\"変更ファイル数: {len(data['data']['git']['changes']['files_modified'])}\")
    print(f\"削除ファイル数: {len(data['data']['git']['changes']['files_deleted'])}\")
"
            fi
        else
            echo "出力ディレクトリが見つかりません"
        fi
    else
        echo "デモを実行するには、少なくとも2つのコミットが必要です"
        echo ""
        echo "コミットを作成する例:"
        echo "  git add ."
        echo "  git commit -m \"Initial commit\""
        echo "  # 何か変更を加える"
        echo "  git add ."
        echo "  git commit -m \"Second commit\""
    fi
else
    echo "Gitリポジトリが初期化されていません"
    echo ""
    echo "Gitリポジトリを初期化する:"
    echo "  git init"
    echo "  git add ."
    echo "  git commit -m \"Initial commit\""
fi

echo ""
echo "========================================"
echo "デモ完了"
echo "========================================"
