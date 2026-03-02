# 6. GitHubActionsの使用方法<!-- omit in toc -->

GitHub ActionsでClaude Codeを使用するためのセットアップ手順と運用方法について記載する。

## 目次<!-- omit in toc -->

- [6.1. 概要](#61-概要)
- [6.2. 前提条件](#62-前提条件)
- [6.3. AWS設定（Bedrock使用時）](#63-aws設定bedrock使用時)
  - [6.3.1. OIDC Identity Providerの設定](#631-oidc-identity-providerの設定)
  - [6.3.2. IAMポリシーの作成](#632-iamポリシーの作成)
  - [6.3.3. IAMロールの作成](#633-iamロールの作成)
- [6.4. GitHub設定](#64-github設定)
  - [6.4.1. Repository Secretsの設定](#641-repository-secretsの設定)
  - [6.4.2. Actions権限の設定](#642-actions権限の設定)
- [6.5. ワークフローファイルの作成](#65-ワークフローファイルの作成)
  - [6.5.1. 基本的なワークフロー](#651-基本的なワークフロー)
  - [6.5.2. AWS Bedrock使用時のワークフロー](#652-aws-bedrock使用時のワークフロー)
  - [6.5.3. カスタマイズ例](#653-カスタマイズ例)
- [6.6. CLAUDE.mdの設定](#66-claudemdの設定)
- [6.7. サブエージェントの設定](#67-サブエージェントの設定)
- [6.8. 使い方](#68-使い方)
  - [6.8.1. Issueでの使用](#681-issueでの使用)
  - [6.8.2. PRでの使用](#682-prでの使用)
- [6.9. トラブルシューティング](#69-トラブルシューティング)

## 6.1. 概要

GitHub ActionsでClaude Codeを使用するには、以下のセットアップが必要：

1. **認証設定**: Anthropic API または AWS Bedrock
2. **GitHub設定**: Secrets、権限
3. **ワークフローファイル**: `.github/workflows/`に配置
4. **プロジェクト設定**: CLAUDE.md、サブエージェント定義

## 6.2. 前提条件

- GitHubリポジトリへのAdmin権限
- Anthropic APIキー または AWS Bedrockへのアクセス権
- （Bedrock使用時）AWSアカウントとIAM管理権限

## 6.3. AWS設定（Bedrock使用時）

AWS Bedrockを使用する場合のセットアップ手順。Anthropic APIを直接使用する場合はスキップ可能。

### 6.3.1. OIDC Identity Providerの設定

**手順**:
AWS Management Console > IAM > IDプロバイダ > プロバイダを追加

**設定値**:
```
Provider type: OpenID Connect
Provider URL: https://token.actions.githubusercontent.com
Audience: sts.amazonaws.com
```

### 6.3.2. IAMポリシーの作成

> **注意**: 以下のIAMポリシーは基本的な設定例である。本番環境での使用時は、セキュリティ要件に応じて調整すること。

**手順**:
AWS Management Console > IAM > ポリシー > ポリシーの作成

**ポリシーJSON**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "BedrockInvoke",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": [
        "arn:aws:bedrock:*::foundation-model/anthropic.claude-*"
      ]
    }
  ]
}
```

**ポリシー名**: `GitHubActionsClaudeBedrockPolicy`

### 6.3.3. IAMロールの作成

**手順**:
AWS Management Console > IAM > ロール > ロールを作成

**信頼関係ポリシー**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::[ACCOUNT-ID]:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:[OWNER]/[REPO]:*"
        }
      }
    }
  ]
}
```

**注意**: `[ACCOUNT-ID]`、`[OWNER]`、`[REPO]`を実際の値に置き換え

**ロール名**: `GitHubActionsClaudeRole`

**アタッチするポリシー**: `GitHubActionsClaudeBedrockPolicy`

## 6.4. GitHub設定

### 6.4.1. Repository Secretsの設定

**手順**:
Settings > Secrets and variables > Actions > New repository secret

**Anthropic API使用時**:
| 変数名 | 値の例 | 説明 |
|--------|--------|------|
| `ANTHROPIC_API_KEY` | `sk-ant-api...` | Anthropic APIキー |

**AWS Bedrock使用時**:
| 変数名 | 値の例 | 説明 |
|--------|--------|------|
| `AWS_ROLE_ARN` | `arn:aws:iam::[ACCOUNT-ID]:role/GitHubActionsClaudeRole` | IAMロールARN |
| `AWS_REGION` | `us-east-1` | AWSリージョン |

### 6.4.2. Actions権限の設定

**手順**:
Settings > Actions > General

**必要な設定**:
1. "Read and write permissions"を有効化
2. "Allow GitHub Actions to create and approve pull requests"をチェック

## 6.5. ワークフローファイルの作成

### 6.5.1. 基本的なワークフロー

**ファイル**: `.github/workflows/claude.yml`

```yaml
name: Claude Code Action

on:
  issue_comment:
    types: [created]
  pull_request_review_comment:
    types: [created]
  issues:
    types: [opened, assigned]
  pull_request:
    types: [opened, synchronize]

jobs:
  claude:
    # @claudeメンションまたは特定イベントで実行
    if: |
      (github.event_name == 'issue_comment' && contains(github.event.comment.body, '@claude')) ||
      (github.event_name == 'pull_request_review_comment' && contains(github.event.comment.body, '@claude')) ||
      (github.event_name == 'issues' && github.event.action == 'assigned') ||
      (github.event_name == 'pull_request')

    runs-on: ubuntu-latest
    timeout-minutes: 60

    # 同じIssue/PRでの実行を直列化
    concurrency:
      group: claude-${{ github.event.issue.number || github.event.pull_request.number }}
      cancel-in-progress: false

    permissions:
      contents: write
      pull-requests: write
      issues: write
      id-token: write

    steps:
      - name: Run Claude
        uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
```

### 6.5.2. AWS Bedrock使用時のワークフロー

```yaml
name: Claude Code Action (Bedrock)

on:
  issue_comment:
    types: [created]
  pull_request_review_comment:
    types: [created]

jobs:
  claude:
    if: |
      (github.event_name == 'issue_comment' && contains(github.event.comment.body, '@claude')) ||
      (github.event_name == 'pull_request_review_comment' && contains(github.event.comment.body, '@claude'))

    runs-on: ubuntu-latest
    timeout-minutes: 60

    concurrency:
      group: claude-${{ github.event.issue.number || github.event.pull_request.number }}
      cancel-in-progress: false

    permissions:
      contents: write
      pull-requests: write
      issues: write
      id-token: write

    steps:
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: ${{ secrets.AWS_REGION }}

      - name: Run Claude
        uses: anthropics/claude-code-action@v1
        with:
          use_bedrock: true
          aws_region: ${{ secrets.AWS_REGION }}
          model: anthropic.claude-sonnet-4-20250514-v1:0
```

### 6.5.3. カスタマイズ例

**ツール制限付きワークフロー**:
```yaml
- name: Run Claude
  uses: anthropics/claude-code-action@v1
  with:
    anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
    allowed_tools: "Read,Grep,Glob,Write,Edit"
    # Bash, WebFetchなどを制限
```

**カスタム指示付きワークフロー**:
```yaml
- name: Run Claude
  uses: anthropics/claude-code-action@v1
  with:
    anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
    custom_instructions: |
      - 日本語で応答してください
      - コードにはコメントを追加してください
      - テストも一緒に作成してください
```

**特定ラベルでのみ実行**:
```yaml
jobs:
  claude:
    if: |
      github.event_name == 'issue_comment' &&
      contains(github.event.comment.body, '@claude') &&
      contains(github.event.issue.labels.*.name, 'claude-enabled')
```

## 6.6. CLAUDE.mdの設定

リポジトリルートに`CLAUDE.md`を配置して、プロジェクト固有の指示を設定。

**ファイル**: `CLAUDE.md`

```markdown
# プロジェクト設定

## 概要
このリポジトリはXXXシステムのバックエンドAPIです。

## 技術スタック
- Python 3.11
- FastAPI
- PostgreSQL
- pytest

## ディレクトリ構造
- src/: ソースコード
- tests/: テストコード
- docs/: ドキュメント

## コーディング規約
- PEP 8準拠
- 型ヒント必須
- docstring形式: Google style

## 重要な注意事項
- 環境変数は .env ファイルで管理（コミット禁止）
- データベースマイグレーションは alembic を使用
- テストは pytest で実行（カバレッジ80%以上）

## コマンド
- テスト実行: `pytest tests/`
- リント: `ruff check src/`
- フォーマット: `ruff format src/`
```

## 6.7. サブエージェントの設定

`.claude/agents/`ディレクトリにサブエージェント定義ファイルを配置。

**ファイル**: `.claude/agents/code-reviewer.md`

```markdown
---
name: code-reviewer
description: コードレビュー専門のサブエージェント
model: sonnet
tools:
  - Read
  - Grep
  - Glob
---

# Code Reviewer

あなたはコードレビューの専門家です。

## レビュー観点
1. **コード品質**: 可読性、保守性、命名規則
2. **セキュリティ**: 脆弱性、入力検証、認証
3. **パフォーマンス**: 効率性、リソース使用
4. **テスト**: カバレッジ、エッジケース

## 出力形式
レビュー結果は以下の形式で出力：
- 🔴 Critical: 即座に修正が必要
- 🟡 Major: 次回リリースまでに修正
- 🟢 Minor: 時間があるときに修正
- 💡 Suggestion: より良い実装パターンの提案
```

## 6.8. 使い方

### 6.8.1. Issueでの使用

**新規タスク依頼**:
```markdown
@claude 以下のタスクを実行してください：

## タスク
ユーザー認証APIにレート制限機能を追加

## 要件
- 1分間に10回までのリクエスト制限
- 制限超過時は429エラーを返す
- Redis使用（既存の接続を利用）

## 対象ファイル
- src/api/auth.py
- src/utils/rate_limit.py（新規作成）
```

**フォローアップ指示**:
```markdown
@claude 前回の実装に加えて、以下の修正をお願いします：
- テストケースを追加
- ドキュメントを更新
```

### 6.8.2. PRでの使用

**コードレビュー依頼**:
```markdown
@claude このPRをレビューしてください。
特にセキュリティとパフォーマンスの観点でチェックをお願いします。
```

**修正依頼**:
```markdown
@claude レビューコメントの指摘事項を修正してください。
```

## 6.9. トラブルシューティング

### 6.9.1. 実行が開始されない

**確認事項**:
1. ワークフローファイルが正しい場所にあるか（`.github/workflows/`）
2. `@claude`の記述が正確か（大文字小文字、スペース）
3. GitHub Actionsが有効か（Settings > Actions）
4. 必要な権限が設定されているか

### 6.9.2. 認証エラー

**Anthropic API**:
```
Error: Invalid API key
```
→ `ANTHROPIC_API_KEY`の値を確認

**AWS Bedrock**:
```
Error: Access Denied
```
→ IAMロールの信頼関係とポリシーを確認

### 6.9.3. タイムアウト

```
Error: Job timeout
```
→ `timeout-minutes`を増やす（最大360分）

### 6.9.4. 権限エラー

```
Error: Resource not accessible by integration
```
→ GitHub Actionsの権限設定を確認
→ `permissions`ブロックの設定を確認

### 6.9.5. コンフリクト

```
Error: Merge conflict
```
→ ベースブランチを最新にしてから再実行
→ 手動でコンフリクトを解決

### 6.9.6. ログの確認方法

1. GitHub > Actions タブ
2. 対象のワークフロー実行を選択
3. ジョブ名をクリック
4. ステップごとのログを確認

***

[目次](./01_はじめに.md#目次)
