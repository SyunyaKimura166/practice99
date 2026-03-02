# 結合テスト仕様書<!-- omit in toc -->

## 目次<!-- omit in toc -->

- [はじめに](#はじめに)
- [1. 前提・対象範囲](#1-前提対象範囲)
- [2. テストケース一覧](#2-テストケース一覧)
- [3. 観点別チェックリスト](#3-観点別チェックリスト)
- [4. トレースマトリクス](#4-トレースマトリクス)

## はじめに

本書は、マルチエージェントシステム（25年3Q）における結合テスト仕様を定義する。

### 目的

マルチエージェントシステムを構成する各Agent間のインタラクションが正しく機能することを検証し、システム全体の結合品質を確保する。

### 対象読者

- マルチエージェントシステムの開発者
- テスト担当者
- プロジェクト管理者

### 関連資料

- [マルチエージェントシステム構成図](/home/ubuntu/review-work/マルチエージェントシステム構成図1.png)
- [DirectorAgentの概要](../02_DirectorAgentの概要.md)
- [エージェント間インターフェース](../05_エージェント間インターフェース.md)

### 暫定事項について

> **注記**: 本仕様は概要レベルの定義であり、各テストケースの詳細テスト手順（前提条件、テストデータ、期待結果、後処理等）は別途策定予定である。仕様の詳細化に伴い、内容が変更される可能性がある。

---

## 1. 前提・対象範囲

- **対象**: マルチエージェントシステム（25年3Q）
- **対象インタラクション**
  1. DirectorAgent → Issueステータス変更
  2. Issueタグ確認 → DevPlannerAgent
  3. Issueタグ確認 → 不具合分析Agent
  4. DevPlannerAgent → dora2 Local MCPサーバ
  5. Dora2 Local MCPサーバ → dora2
  6. dora2 → RequirementAgent
  7. dora2 → DesignAgent
  8. dora2 → CodingAgent
  9. dora2 → TestAgent
  10. dora2 → ReviewAgent
  11. dora2 → DocumentationAgent
  12. DevPlannerAgent → SQS
  13. 不具合分析Agent → SQS
  14. SQS → CICD PipelineAgent
  15. SQS → MLOpsAgent
  16. CICD PipelineAgent → AWSサービス
  17. MLOpsAgent → AWSサービス
  18. DevPlannerAgent → Issue登録
  19. 不具合分析Agent → Issue登録
  20. RequirementAgent → コンテキストの基となる情報をS3登録
  21. S3 → ContextAgent
  22. ContextAgent → RDB登録
  23. RDB → ContextAgent
  24. ContextAgent → GitHub
  25. GitHub → RequirementAgent

---

## 2. テストケース一覧

| ID | タイトル | 目的 |
|---|---|---|
| TC-01 | DirectorAgentによるIssueステータス変更 | ステータス遷移の正当性と監査ログ |
| TC-02 | Issueタグ確認でDevPlannerAgent起動 | タグ→起動条件発火 |
| TC-03 | Issueタグ確認で不具合分析Agent起動 | バグタグ→起動条件発火 |
| TC-04 | DevPlannerAgent→dora2 Local MCP連携 | 出力PushとMCP呼び出し |
| TC-05 | Local MCP→dora2ブリッジ | ローカル→クラウドの透過連携 |
| TC-06 | dora2→RequirementAgent | 要件生成／更新フロー起動 |
| TC-07 | dora2→DesignAgent | 設計生成／更新フロー起動 |
| TC-08 | dora2→CodingAgent | コーディング指示生成／更新 |
| TC-09 | dora2→TestAgent | テスト生成／更新 |
| TC-10 | dora2→ReviewAgent | レビュー課題生成 |
| TC-11 | dora2→DocumentationAgent | 文書生成／更新 |
| TC-12 | DevPlannerAgent→SQS送信 | イベント送信とDLQ制御 |
| TC-13 | 不具合分析Agent→SQS送信 | バグイベント送信 |
| TC-14 | SQS→CICD PipelineAgent受信 | キューからパイプライン起動 |
| TC-15 | SQS→MLOpsAgent受信 | 学習/推論フロー起動 |
| TC-16 | CICD PipelineAgent→AWSサービス | CodePipeline/Build/Deploy連携 |
| TC-17 | MLOpsAgent→AWSサービス | SageMaker等連携 |
| TC-18 | DevPlannerAgent→Issue登録 | 新規Issue作成 |
| TC-19 | 不具合分析Agent→Issue登録 | バグIssue作成 |
| TC-20 | RequirementAgent→S3登録 | コンテキストデータS3保存 |
| TC-21 | S3→ContextAgent | S3イベントで取り込み |
| TC-22 | ContextAgent→RDB登録 | RDBへ正規化保存 |
| TC-23 | RDB→ContextAgent | 参照/更新/逆引き |
| TC-24 | ContextAgent→GitHub | 生成物のGitHub反映 |
| TC-25 | GitHub→RequirementAgent | GitHubイベントから要件更新 |

---

## 3. 観点別チェックリスト

### メッセージ/イベント共通

- [ ] correlation_id, event_type, source, timestamp の4点が必ず含まれる
- [ ] 失敗時は retry_count と last_error を記録
- [ ] DLQ に移送した場合、復旧手順がログに記載

### セキュリティ/IAM

- [ ] 最小権限のIAMロールで成功
- [ ] GitHubトークンは環境秘密管理（Actions Secrets）で保護
- [ ] S3はKMS暗号化、RDSは接続暗号化/TLS

### スキーマ/整合性

- [ ] dora2→Agentのpayloadに schema_version が含まれる
- [ ] RDB正規化（FK, UNIQUE, NOT NULL）が満たされる
- [ ] GitHub連携ではコミット署名検証が通る

### 可観測性

- [ ] すべてのコンポーネントで構造化ログ（JSON）出力
- [ ] メトリクス（成功率、レイテンシ、キュー滞留）を記録
- [ ] アラート閾値の試験（ビルド失敗、SageMaker失敗、SQS滞留）

---

## 4. トレースマトリクス

| インタラクション | テストケース |
|---|---|
| DirectorAgent→Issueステータス変更 | TC-01 |
| Issueタグ確認→DevPlannerAgent | TC-02 |
| Issueタグ確認→不具合分析Agent | TC-03 |
| DevPlannerAgent→dora2 Local MCPサーバ | TC-04 |
| Dora2 Local MCPサーバ→dora2 | TC-05 |
| dora2→RequirementAgent | TC-06 |
| dora2→DesignAgent | TC-07 |
| dora2→CodingAgent | TC-08 |
| dora2→TestAgent | TC-09 |
| dora2→ReviewAgent | TC-10 |
| dora2→DocumentationAgent | TC-11 |
| DevPlannerAgent→SQS | TC-12 |
| 不具合分析Agent→SQS | TC-13 |
| SQS→CICD PipelineAgent | TC-14 |
| SQS→MLOpsAgent | TC-15 |
| CICD PipelineAgent→AWSサービス | TC-16 |
| MLOpsAgent→AWSサービス | TC-17 |
| DevPlannerAgent→Issue登録 | TC-18 |
| 不具合分析Agent→Issue登録 | TC-19 |
| RequirementAgent→S3登録 | TC-20 |
| S3→ContextAgent | TC-21 |
| ContextAgent→RDB登録 | TC-22 |
| RDB→ContextAgent | TC-23 |
| ContextAgent→GitHub | TC-24 |
| GitHub→RequirementAgent | TC-25 |
