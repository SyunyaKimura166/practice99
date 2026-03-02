# 2. DirectorAgentの概要<!-- omit in toc -->

## 目次<!-- omit in toc -->

- [2.1. 概要](#21-概要)
- [2.2. 実行環境](#22-実行環境)
- [2.3. Issue種別](#23-issue種別)
- [2.4. GitHub Projectsステータス](#24-github-projectsステータス)
- [2.5. 優先度判断の観点](#25-優先度判断の観点)
- [2.6. タスク振り分け先（マネージャエージェント）](#26-タスク振り分け先マネージャエージェント)
- [2.7. 実行契機](#27-実行契機)
- [2.8. エージェント構成](#28-エージェント構成)

## 2.1. 概要

DirectorAgentは、マルチエージェントシステムにおける**司令塔**として機能する。GitHub Issuesに登録されたタスクをMCPサーバ経由で取得し、優先度を判断して適切なマネージャエージェントへ振り分ける役割を担う。

**主要責務**:
1. GitHub Projects MCP Server経由でBacklogステータスのissue一覧を取得
2. 複数の観点から優先度を判断し、最も優先度の高いissueを選択
3. Issue本文の`assignees`フィールドを編集して担当エージェントを設定（MCP経由）
4. GitHub Projectsのステータスを「Backlog」から「Ready」に変更（MCP経由）
5. マネージャエージェントがポーリングで検知し、「Running」に変更して着手

---

## 2.2. 実行環境

DirectorAgentは、 **GitHub ActionsのClaude Code（Claude Opus 4.5）** を使用して実現する。

### 2.2.1. 構成要素

```
GitHub Actions Workflow
    ↓
Claude Code (claude-code action)
    ↓ (MCP over STDIO)
GitHub Projects MCP Server (FastMCP)
    ↓ (GraphQL API)
GitHub Projects V2
```

### 2.2.2. MCPサーバ

**ファイル**: `./mcp_tool/github_projects_mcp.py`

**提供ツール**:
| ツール名 | 説明 | DirectorAgentでの用途 | 使用頻度 |
|----------|------|----------------------|----------|
| `list_repository_issues` | リポジトリのissue一覧を取得 | Backlog Issue一覧取得 | 実行毎に1回 |
| `get_issue_project_info` | Issueのプロジェクト情報とステータスを取得 | Issue詳細・プロジェクト情報取得 | Issue毎に1回 |
| `update_project_status` | プロジェクトアイテムのステータスを変更 | ステータス変更（内部処理） | 必要に応じて |
| `get_issue_node_id_from_repo_info` | リポジトリ情報からIssue Node IDを取得 | Issue特定 | 必要に応じて |
| `change_issue_status_by_repo_info` | リポジトリ情報を使ってステータスを変更 | Backlog→Ready変更 | 選択Issue毎に1回 |
| `change_issue_status_by_node_id` | Node IDを使ってステータスを変更 | Backlog→Ready変更 | 必要に応じて |
| `update_issue_assignees` | Issue本文のassigneesフィールドを変更 | 担当エージェント設定 | 選択Issue毎に1回 |

**DirectorAgentのMCP操作フロー**:
```
1. list_repository_issues(owner, repo, state="open")
   → Backlog Issue一覧取得

2. get_issue_project_info(issue_node_id)
   → 各IssueのProject情報・ステータス確認

3. [LLMによる優先度判断・振り分け決定]

4. update_issue_assignees(owner, repo, issue_number, assignees)
   → 担当エージェント設定（devplanner or bug-analysis）

5. change_issue_status_by_repo_info(owner, repo, issue_number, "Backlog", "Ready")
   → ステータス変更（Backlog → Ready）
```

**担当エージェント設定の現在・将来方式**:
- **現在方式**: Issue本文の`assignees: []`フィールドを直接編集
- **利点**: 既存Issueテンプレートとの互換性、シンプルな実装
- **課題**: 本文編集による意図しない変更リスク
- **将来検討**: GitHubラベル、GitHub Projects V2カスタムフィールド等

### 2.2.3. GitHub Actionsワークフロー設定例

```yaml
name: DirectorAgent

on:
  workflow_dispatch:  # Phase 1: 手動実行
  schedule:           # Phase 2: 定期実行
    - cron: '0 */6 * * *'  # 6時間毎

jobs:
  director:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      issues: write
      pull-requests: write
    steps:
      - uses: actions/checkout@v4

      - name: Run DirectorAgent
        uses: anthropics/claude-code-action@v1
        with:
          prompt: |
            BacklogステータスのIssueを取得し、優先度を判断して
            最も優先度の高いIssueのステータスをReadyに変更してください。
          mcp_config: |
            {
              "mcpServers": {
                "github-projects": {
                  "command": "python",
                  "args": ["github_projects_mcp.py"]
                }
              }
            }
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

---

## 2.3. Issue種別

DirectorAgentが扱うissueは、Issueテンプレートに基づき分類される。現在定義されている種別は以下の通りだが、**テンプレートの変更に柔軟に対応できる設計**としている：

| 種別 | 英語名 | 説明 | 主な振り分け先 |
|------|--------|------|-----------|
| 新規開発 | New Development | 新しい機能やシステムの開発 | DevPlanner |
| 機能追加 | Feature | 既存システムへの機能追加 | DevPlanner |
| 不具合修正 | Bug | 不具合・バグの修正 | 不具合分析 |
| リファクタ | Refactor | コードの構造改善・最適化 | DevPlanner |
| 調査/分析 | Research | 技術調査や分析タスク | DevPlanner |
| パフォーマンス改善 | Perf | 処理速度・リソース効率の改善 | DevPlanner |
| セキュリティ | Security | セキュリティ対策・脆弱性修正 | DevPlanner |
| ドキュメント | Docs | ドキュメント作成・更新 | DevPlanner |
| PoC / プロトタイプ | Proof of Concept | 技術検証・プロトタイプ作成 | DevPlanner |

**テンプレート変更への耐性**:
- 新しい種別が追加されても、LLM（Claude Opus 4.5）が意味を理解して適切に処理
- 固定的なパターンマッチではなく、自然言語理解に基づく解析
- 種別名の変更や追加時も再デプロイ不要

**Issueテンプレート**: [template.md](./issue_template/template.md)

---

## 2.4. GitHub Projectsステータス

DirectorAgentは、以下のステータスを使用してissueの進捗を管理する：

| ステータス | 説明 | 遷移元 | 遷移先 |
|-----------|------|--------|--------|
| **Backlog** | 新規登録、未着手 | - | Ready |
| **Ready** | DirectorAgentが選択、着手待ち | Backlog | Running |
| **Running** | マネージャエージェントが実行中 | Ready | Review |
| **Review** | レビュー中 | Running | Merged / Reject |
| **Reject** | リジェクト、再検討が必要 | Review | Backlog |
| **Merged** | 完了、マージ済み | Review | - |

### 2.4.1. ステータス遷移図

```
┌─────────┐
│ Backlog │ ←────────────────────────────────┐
└────┬────┘                                  │
     │ DirectorAgentが優先度判断              │
     ↓                                       │
┌─────────┐                                  │
│  Ready  │ ← マネージャエージェントがポーリング│
└────┬────┘                                  │
     │ マネージャエージェントが着手            │
     ↓                                       │
┌─────────┐                                  │
│ Running │                                  │
└────┬────┘                                  │
     │ 実装完了、PR作成                       │
     ↓                                       │
┌─────────┐                                  │
│ Review  │                                  │
└────┬────┘                                  │
     │                                       │
     ├──→ ┌────────┐                         │
     │    │ Merged │ (完了)                  │
     │    └────────┘                         │
     │                                       │
     └──→ ┌────────┐ ────────────────────────┘
          │ Reject │ (再検討が必要)
          └────────┘
```

---

## 2.5. 優先度判断の観点

DirectorAgentは、「Tidy First?」の考え方を参考に、以下の観点から優先度を総合的に判断する：

### 2.5.1. 優先度判断観点一覧

| 優先度 | 観点 | 重み（例） | 説明 |
|--------|------|----------|------|
| 1 | 顧客からの要求 | 1.5 | 顧客から直接要望されたタスク |
| 2 | ユーザーの不満 | 1.3 | ユーザーフィードバックに基づく改善要求 |
| 3 | マーケティング効果 | 1.2 | 自社プロダクトと市場ニーズを踏まえた効果 |
| 4 | セキュリティ（Critical） | 1.5 | 緊急性の高いセキュリティ対策 |
| 5 | 不具合修正（Critical） | 1.4 | システム停止レベルの重大な不具合 |
| 6 | 不具合修正（Major） | 1.1 | 機能に影響する不具合 |
| 7 | 不具合修正（Minor） | 0.9 | 軽微な不具合・改善 |
| 8 | 既存機能改善 | 1.0 | 現行機能の品質・使いやすさ向上 |
| 9 | リファクタリング | 0.9 | コード構造・振る舞いの改善 |

### 2.5.2. 優先度スコア計算

現在の優先度計算は運用開始時の暫定的なものであり、実際の運用データに基づく継続的な改善が前提となっている。

**計算方式**:
```
基本スコア = LLM総合評価スコア (1-10)
調整スコア = 基本スコア × 時間係数 × 依存関係係数

時間係数 = 1 + (経過日数 / 30) × 0.1  (最大1.5)
依存関係係数 = 0.8 (他Issue待ち) ～ 1.2 (ブロッカー)
```

**計算例**:
```
Issue: "顧客ログイン時のセキュリティ脆弱性修正"
- LLM総合評価: 8.5 (顧客要求+セキュリティ重要度を総合判断)
- 時間係数: 1.2 (36日経過)
- 依存関係係数: 1.1 (他タスクに影響)
最終スコア: 8.5 × 1.2 × 1.1 = 11.22
```

**特徴**:
- LLM主導の意味理解による総合判断
- 複雑な重み付けテーブルからの解放
- 新しい観点の追加が容易

### 2.5.3. Tidy First?の適用

「Tidy First?」の考え方に基づき、以下の判断を行う：

- **小さな整理（tidying）を先に行うべきか？**
  - 振る舞いの変更より先にコードを整理することで、変更が容易になる場合
  - リファクタリングのissueは、関連する機能追加issueと連携して優先度を判断

---

## 2.6. タスク振り分け先（マネージャエージェント）

DirectorAgentは、**Issueの内容全体を解析し、総合的に判断**して以下のマネージャエージェントへタスクを振り分ける：

### 2.6.1. DevPlanner Agents

**assignees設定値**: `devplanner`

**対象issue種別**:
- 新規開発（New Development）
- 機能追加（Feature）
- リファクタ（Refactor）
- 調査/分析（Research）
- パフォーマンス改善（Perf）
- セキュリティ（Security）
- ドキュメント（Docs）
- PoC / プロトタイプ（Proof of Concept）

**DevPlanner Agentsの責務**:
- タスクの分解
- 実装計画の策定
- 下流エージェント（Coding Agent、Test Agentなど）への指示

### 2.6.2. 不具合分析 Agents

**assignees設定値**: `bug-analysis`

**対象issue種別**:
- 不具合修正（Bug）

**不具合分析 Agentsの責務**:
- 不具合の原因分析
- 再現手順の確認
- 修正方針の策定
- 修正タスクのDevPlanner Agentsへの引き渡し

### 2.6.3. 振り分けロジック（総合判断方式）

DirectorAgentは、以下の情報を総合的に解析してタスク振り分け先を決定する：

**解析対象**:
- Issue種別（テンプレートの「種別」フィールド）
- 要求内容（「要求」フィールド）
- 背景・目的（「背景・目的」フィールド）
- スコープ（「スコープ」フィールド）
- 要件（「要件」フィールド）
- Issue本文全体のコンテキスト

**基本的な振り分けルール**:
```
1. Issue内容全体をLLM（Claude Opus 4.5）が解析
2. 以下の観点から振り分け先を判断：
   - 種別が「Bug」または不具合に関する内容 → 不具合分析 Agents
   - それ以外（開発、機能追加、リファクタ等） → DevPlanner Agents
3. 境界ケースはIssue内容の詳細を踏まえて総合判断
```

**判断理由の記録**:
- 振り分け時に判断理由を実行レポートに記録
- 後からの検証・改善に活用

### 2.6.4. マネージャエージェントの検知方式

マネージャエージェントは、以下の方式でタスクを検知する：

1. **ポーリング**: 定期的にGitHub Projectsをチェック
2. **検知条件**:
   - ステータス = "Ready"
   - assignees = 自エージェント担当（devplanner or bug-analysis）
3. **着手処理**:
   - ステータスを"Running"に変更
   - 処理開始

**assigneesの用途拡張**:
- マネージャエージェントからワーカーエージェントへのタスク割り振りにも同じ仕組みを使用
- 例: `assignees: [coding-agent]`、`assignees: [test-agent]`

---

## 2.7. 実行契機

DirectorAgentは段階的に進化する実行契機を採用し、安全で確実なシステム導入と運用を実現する：

### 2.7.1. Phase 1: 手動実行

**実行契機**: 開発者やプロジェクトマネージャーによる手動実行

**トリガー方法**:
- GitHub ActionsのUIから「Run workflow」ボタンをクリック
- `workflow_dispatch`イベントによる手動トリガー

**適用場面**:
- システムの動作検証、緊急時の優先度判断、新機能のテスト
- 開発初期段階での動作確認

**メリット**: 安全性が高く、実行タイミングを完全にコントロール可能

**実行フロー**:
1. 開発者がGitHub Actionsページで「DirectorAgent」ワークフローを選択
2. 「Run workflow」ボタンをクリックして手動実行
3. DirectorAgentが優先度判断とタスク振り分けを実行
4. マネージャエージェントがポーリングで検知して処理開始

### 2.7.2. Phase 2: 定期実行

**実行契機**: 設定されたスケジュール（例：6時間毎）で自動実行

**トリガー方法**:
- GitHub Actionsのcron設定による定期実行
- `schedule`イベントでの自動トリガー

**適用場面**:
- 安定運用段階での定期的なタスク管理
- 人手の介入を最小化した継続運用

**メリット**: 人の判断に依存せず、一定間隔でのタスク管理を実現

**設定例**:
```yaml
on:
  schedule:
    - cron: '0 */6 * * *'  # 6時間毎
```

### 2.7.3. Phase 3: 自動実行

**実行契機**: AI による総合的な状況判断に基づく自動実行

**自動実行の判断基準**:
- マネージャエージェントの現在の稼働状況
- Backlog Issueの蓄積状況と緊急度評価
- システムリソースの使用状況
- 過去の実行履歴に基づく最適化判断

**トリガー方法**:
- カスタムエージェントによる状況監視と実行判断
- 複数の条件を総合的に評価した自動実行

**適用場面**:
- 完全自動化された開発環境での無人運用
- 最適なタイミングでの実行によるシステム効率最大化

**メリット**: 最適なタイミングでの実行により、システム全体の効率を最大化

---

## 2.8. エージェント構成

DirectorAgentは、マルチエージェントシステムの最上位に位置する：

| # | エージェント種別 | エージェント名 | 主要責務 |
|---|----------------|--------------|----------|
| **1** | Director | **Director Agent** | **Issue管理、優先度判断、タスク振り分け** |
| 2 | マネージャ | DevPlanner Agent | タスク分解、エージェント割り当て |
| 3 | マネージャ | 不具合分析 Agent | 不具合原因分析、修正方針策定 |
| 4 | ワーカー | Requirement Agent | 要件定義書作成 |
| 5 | ワーカー | Design Agent | システム設計、アーキテクチャ設計 |
| 6 | ワーカー | Coding Agent | コード実装、単体テスト作成 |
| 7 | ワーカー | Debug Agent | バグ修正、デバッグ |
| 8 | ワーカー | Test Agent | テスト自動化、実行 |
| 9 | ワーカー | Review Agent | コードレビュー、品質チェック |
| 10 | ワーカー | Documentation Agent | ドキュメント作成、更新 |
| 11 | ワーカー | Integration Agent | 統合テスト、デプロイ管理 |
| 12 | ワーカー | CI/CD Pipeline Agent | CI/CD パイプライン管理 |
| 13 | ワーカー | MLOps Agent | MLOps管理 |

**エージェント階層**:

```
                  ┌─────────────────┐
                  │  Director Agent │
                  └────────┬────────┘
                           │
          ┌────────────────┴────────────────┐
          ↓                                 ↓
┌──────────────────┐              ┌──────────────────┐
│ DevPlanner Agent │              │ 不具合分析 Agent  │
└────────┬─────────┘              └─────────┬────────┘
         │                                  │
         ↓                                  ↓
┌───────────────────────────────────────────────────┐
│ Coding / Test / Review / Design / Documentation   │
│ / Integration / Debug / Requirement               │
│ / CI/CD Pipeline / MLOps                          │
└───────────────────────────────────────────────────┘
```

***

[目次](./01_はじめに.md#はじめに)
