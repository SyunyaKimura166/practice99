# DirectorAgent

マルチエージェントシステムの司令塔 - GitHub Issuesの優先度判断とタスク振り分けエージェント

## 概要

DirectorAgentは、ソフトウェア開発プロセスにおける意思決定の自動化と品質向上を担う中核エージェントです。GitHub Issuesに登録されたタスクの優先度を判断し、適切な専門エージェント（DevPlanner Agents / 不具合分析 Agents）にタスクを振り分けます。

**主な機能:**
- GitHub Issues（Backlogステータス）からタスク一覧を取得
- Claude Opus 4.5による優先度判断（「Tidy First?」思想を適用）
- タスク種別に応じたマネージャエージェントへの振り分け
- GitHub Projectsステータスの自動更新（Backlog → Ready）

## プロジェクト構成

```
Director/
├── .github/
│   └── workflows/
│       └── DirectorAgentWorkflow.yml  # GitHub Actionsワークフロー
├── docs/
│   ├── IntegrationTest/            # 統合テスト仕様
│   │   └── integration_test_spec.md
│   ├── SystemTest/                 # システムテスト
│   │   └── VAD_System_Test_Scenario.md
│   ├── requirement/                # 要件定義書
│   │   ├── 01_はじめに.md
│   │   ├── 02_DirectorAgentの概要.md
│   │   ├── 03_機能要件.md
│   │   ├── 04_非機能要件.md
│   │   ├── 05_エージェント間インターフェース.md
│   │   ├── 06_シーケンス図.md
│   │   ├── create/                 # 作成プロンプト・参考資料
│   │   ├── issue_template/         # Issueテンプレート
│   │   │   ├── template.md
│   │   │   └── example.md
│   │   ├── mcp_tool/               # GitHub Projects MCP Server
│   │   │   ├── github_projects_mcp.py
│   │   │   └── requirements.txt
│   │   ├── prompt/                 # DirectorAgentプロンプト
│   │   │   └── DirectorAgentPrompt.md
│   │   └── review/                 # レビュー関連
│   └── research/                   # 調査報告書
│       ├── GitHubActions/          # GitHub Actions調査
│       │   ├── 01_はじめに.md
│       │   ├── 02_GitHubActionsの動作の実態.md
│       │   ├── 03_同時並行でのワークフロー実行.md
│       │   ├── 04_EC2上ClaudeAgentSDKとの違い.md
│       │   ├── 05_参照するコンテキスト範囲.md
│       │   ├── 06_GitHubActionsの使用方法.md
│       │   ├── create/
│       │   └── review/
│       └── VAD-Autoware/           # VAD・Autoware比較調査
│           ├── 01_VADとAutowareの比較.md
│           ├── create/             # 作成プロンプト・参考資料
│           └── review/             # レビュー関連
├── sample/                         # サンプルファイル
│   └── directoragent_run.md        # EC2上での動作確認結果まとめ資料
├── .gitignore
└── README.md                       # 本ファイル
```

## Issue種別

DirectorAgentは以下の9種類のIssueを処理します：

| 種別 | 英語名 | 振り分け先 |
|------|--------|-----------|
| 新規開発 | New Development | DevPlanner Agents |
| 機能追加 | Feature | DevPlanner Agents |
| 不具合修正 | Bug | 不具合分析 Agents |
| リファクタ | Refactor | DevPlanner Agents |
| 調査/分析 | Research | DevPlanner Agents |
| パフォーマンス改善 | Perf | DevPlanner Agents |
| セキュリティ | Security | DevPlanner Agents |
| ドキュメント | Docs | DevPlanner Agents |
| PoC / プロトタイプ | Proof of Concept | DevPlanner Agents |

## 優先度判断の観点

DirectorAgentは以下の観点から優先度を総合的に判断します：

1. **顧客からの要求** - 顧客から直接要望されたタスク
2. **ユーザーの不満** - ユーザーフィードバックに基づく改善要求
3. **マーケティング効果** - 市場ニーズを踏まえた効果の高いもの
4. **セキュリティ（Critical）** - 緊急性の高いセキュリティ対策
5. **不具合修正（Critical/Major/Minor）** - 重大度に応じた不具合対応
6. **既存機能改善** - 現行機能の品質・使いやすさ向上
7. **リファクタリング** - コード構造・振る舞いの改善

## 実行契機

DirectorAgentは段階的に進化する実行契機を採用しています：

| Phase | 実行契機 | 説明 |
|-------|---------|------|
| Phase 1 | 手動実行 | GitHub ActionsのUIから手動で実行 |
| Phase 2 | 定期実行 | スケジュール設定（例：6時間毎）で自動実行 |
| Phase 3 | 自動実行 | AIによる総合的な状況判断に基づく実行 |

## 使い方

### 1. 前提条件

- GitHub リポジトリ
- GitHub Projects V2 の設定
- 以下のSecrets設定:
  - `GITHUB_TOKEN`: GitHub Actions自動発行
  - `ANTHROPIC_API_KEY`: Claude API キー

### 2. GitHub Actionsワークフロー設定

- [.github/workflows/DirectorAgentWorkflow.ym](.github/workflows/DirectorAgentWorkflow.yml)を参照

### 3. Issueテンプレートの準備

Issueテンプレートを配置し、以下のフィールドを含めます：

- Projects ステータス（Backlog, Ready, Running, Review, Reject, Merged）
- 種別（9種類のIssue種別）
- 要求、背景・目的、スコープ、要件

詳細: [Issueテンプレート](.docs/requirement/issue_template/template.md)

## 技術スタック

| 技術要素 | 使用技術 |
|----------|----------|
| 実行環境 | GitHub Actions |
| AIエージェント | Claude Code（Claude Opus 4.5） |
| GitHub連携 | GitHub Projects MCP Server (FastMCP) |
| 通信プロトコル | MCP (Model Context Protocol) |
| ステータス管理 | GitHub Projects V2 |

## エージェント構成

```
                  ┌─────────────────┐
                  │  Director Agent │
                  └────────┬────────┘
                           │
          ┌────────────────┴────────────────┐
          ↓                                 ↓
┌──────────────────┐              ┌──────────────────┐
│ DevPlanner Agent │              │ 不具合分析 Agent  │
│ (devplanner)     │              │ (bug-analysis)   │
└────────┬─────────┘              └─────────┬────────┘
         │                                  │
         ↓                                  ↓
┌───────────────────────────────────────────────────┐
│ Coding / Test / Review / Design / Documentation   │
│ / Integration / Debug / Requirement               │
│ / CI/CD Pipeline / MLOps                          │
└───────────────────────────────────────────────────┘
```

## ステータス遷移

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

## 貢献ガイド

### 貢献方法

1. このリポジトリをフォーク
2. フィーチャーブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

### コミットメッセージ規約

- `feat:` 新機能の追加
- `fix:` バグ修正
- `docs:` ドキュメントの更新
- `refactor:` コードのリファクタリング
- `test:` テストの追加・修正
- `chore:` ビルドプロセスやツールの変更

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## サポート

問題が発生した場合は、以下を確認してください：

1. GitHub ActionsのSecretsが正しく設定されていること
2. GitHub Projects V2が適切に設定されていること
3. Issueテンプレートが正しい形式であること
4. Issueを作成して質問

## ロードマップ

### Phase 1: 基本機能実装（手動実行）

- [ ] GitHub Actions基盤整備
- [ ] MCP Server統合
- [ ] Issue解析・優先度判断ロジック
- [ ] GitHub Projects更新処理
- [ ] 実行レポート生成

### Phase 2: 定期実行・安定化

- [ ] スケジュール実行基盤
- [ ] マネージャエージェント状況監視
- [ ] 自動実行条件判定
- [ ] 統合テスト・安定化

### Phase 3: 完全自動化

- [ ] Manager Agent実装・配置
- [ ] ステータス遷移整合性確保
- [ ] End-to-End統合テスト
- [ ] 運用監視・メンテナンス体制

## 関連リンク

- [Claude Code公式ドキュメント](https://docs.anthropic.com/claude-code)
- [GitHub Projects API](https://docs.github.com/en/graphql)
- [MCP (Model Context Protocol)](https://modelcontextprotocol.io/)
- [Tidy First? ―個人で実践する経験主義的ソフトウェア設計](https://www.oreilly.co.jp/books/9784814400911/)

## 作者

Claude Opus 4.5、HISOL上野

## 更新履歴

### v0.1.0 (2025-01-19)
- 初回リリース
- 要件定義書作成完了
- README.md作成
