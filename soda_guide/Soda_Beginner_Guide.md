# Soda初心者向けガイド

- [Soda初心者向けガイド](#soda初心者向けガイド)
  - [はじめに](#はじめに)
  - [(1) Sodaとは](#1-sodaとは)
    - [Sodaとは](#sodaとは)
    - [Sodaの主な機能](#sodaの主な機能)
    - [Sodaの公式リポジトリ](#sodaの公式リポジトリ)
  - [(2) 前提知識](#2-前提知識)
    - [AWS](#aws)
    - [Claude Code](#claude-code)
    - [Amazon Bedrock AgentCore](#amazon-bedrock-agentcore)
  - [(3) Sodaのドキュメントの「チュートリアル」と「ガイド」](#3-sodaのドキュメントのチュートリアルとガイド)
    - [比較表](#比較表)
    - [チュートリアル（2本）](#チュートリアル2本)
    - [ガイド（5本）](#ガイド5本)
    - [使い分けの例](#使い分けの例)
  - [(4) Sodaのシステム全体構成](#4-sodaのシステム全体構成)
  - [(5) Soda環境構築の手順](#5-soda環境構築の手順)
  - [(6) 変更履歴](#6-変更履歴)

## はじめに
本ドキュメントは、Soda (Software Developer Agents) 初心者向けにXXXXを説明します。

## (1) Sodaとは
### Sodaとは
Soda (Software Developer Agents) は、AWS Bedrock AgentCore上で動作するAIソフトウェアエンジニアリングエージェントです。
Git統合、MCP（Model Context Protocol）サーバー、特化型サブエージェントによるマルチエージェントワークフローをサポートしています。

### Sodaの主な機能
- Git統合
  - リポジトリのクローン、ブランチ管理、自動コミット・プッシュ
- MCPサーバー
  - ローカル/リモートの2つのMCPサーバーを提供
- サブエージェントシステム
  - TDD開発ワークフローを支援する特化型エージェント
- Claude Code連携
  - スキルとサブエージェントによるオーケストレーション

### Sodaの公式リポジトリ
- 公式リポジトリ
  - https://github.com/IoVPF-AgenticSoftwareEngineering/soda

## (2) 前提知識
### AWS
  - AWSアカウントの基本操作（マネジメントコンソールへのログイン、リージョン選択）
  - AWS CLIのインストールと初期設定（`aws configure`）
  - IAMの基本概念（ユーザー、ロール、ポリシー、OIDC）
  - Amazon S3の基本操作（バケット、オブジェクトの概念）
  - Amazon CloudWatch Logsの閲覧方法
  - AWS CloudFormationの基本概念（スタック、テンプレート）
  - Amazon ECRの基本概念（コンテナイメージのリポジトリ）
### Claude Code
  - Claude Code自体、及び、Claude Codeの「Skills」、「Subagent」、「Plugins」、「Rules」
  - https://zenn.dev/heku/books/claude-code-guide
  - https://zenn.dev/tmasuyama1114/books/claude_code_basic
### Amazon Bedrock AgentCore
  - https://dev.classmethod.jp/articles/amazon-bedrock-agentcore-2025-summary/
  - https://dev.classmethod.jp/articles/amazon-bedrock-agentcore-developersio-2025-osaka/

## (3) Sodaのドキュメントの「チュートリアル」と「ガイド」
Sodaの公式リポジトリのドキュメントは、「チュートリアル」と「ガイド」を使い分けています。

### 比較表
| 観点 | チュートリアル | ガイド |
|------|-------------|--------|
| **目的** | 学習指向（Learning-oriented） | 作業指向（Task-oriented） |
| **構成** | ステップバイステップで一連の流れを体験 | 特定トピックごとに分割された手順書 |
| **読み方** | 最初から最後まで順番に進める | 必要な箇所だけ参照する |
| **対象者** | 初めてSodaを使う人 | 基本を理解した上で特定タスクを実行する人 |
| **所要時間** | 明示（開発者: 30〜45分、ユーザー: 15〜20分） | 明示なし（必要な部分だけ読む想定） |
| **前提知識** | 最小限（環境構築から始まる） | チュートリアルまたは一定の知識が前提 |

### チュートリアル（2本）

| ドキュメント | 内容 |
|-------------|------|
| [開発者チュートリアル](docs/guide/tutorial-developer.md) | Python/uv/AWS CLI のインストール → デプロイ → 動作確認 → 運用まで、**一気通貫で体験**する |
| [ユーザーチュートリアル](docs/guide/tutorial-user.md) | デプロイ済みのSodaに対して、AWS CLI設定 → 基本呼び出し → MCP連携まで、**使い始めの流れを体験**する |

→ 初心者が「Sodaとは何か」「何ができるか」を**手を動かしながら理解する**ためのドキュメント

### ガイド（5本）

| ドキュメント | 内容 |
|-------------|------|
| [セットアップガイド](docs/guide/setup.md) | 開発環境構築の詳細手順 |
| [デプロイガイド](docs/guide/deployment.md) | AgentCoreへのデプロイ方法 |
| [使用ガイド](docs/guide/usage.md) | ペイロードパラメータ・サブエージェント指定等の詳細 |
| [MCPガイド](docs/guide/mcp.md) | ローカル/リモートMCPサーバーの設定と使用 |
| [IAMパーミッションガイド](docs/guide/iam-permissions.md) | 必要なAWS権限の詳細 |

→ 特定の作業を行うときに**リファレンスとして参照する**ドキュメント

### 使い分けの例

```
初回利用:
  開発者 → 「開発者チュートリアル」を最初から最後まで実施
  ユーザー → 「ユーザーチュートリアル」を最初から最後まで実施

日常利用:
  「MCP設定を変更したい」→ MCPガイドを参照
  「新しいIAMユーザーを追加したい」→ IAMパーミッションガイドを参照
  「パラメータの詳細を知りたい」→ 使用ガイドを参照
```

## (4) Sodaのシステム全体構成
```mermaid
%%{init: {'theme': 'base', 'themeVariables': {
  'primaryColor': '#232F3E',
  'primaryTextColor': '#ffffff',
  'primaryBorderColor': '#FF9900',
  'lineColor': '#FF9900',
  'secondaryColor': '#37475A',
  'tertiaryColor': '#f0f0f0',
  'fontSize': '14px'
}}}%%
flowchart TB
    subgraph Clients["External Clients"]
        CC["Claude Code / Desktop"]
        GA["GitHub Actions"]
        CLI["CLI / API Client"]
    end

    subgraph AWS["AWS Cloud"]
        subgraph Auth["Amazon Cognito"]
            COG["User Pool<br/>OAuth 2.0 / JWT"]
        end

        subgraph AgentCore["Amazon Bedrock AgentCore"]
            subgraph SodaContainer["Soda Agent Container"]
                EP["soda-general.py"]
                AW["AgentWorkflow<br/>Pre → Agent → Post"]
                CSDK["Claude Agent SDK"]
                subgraph Subagents["Subagents"]
                    SA_SW["spec_writer"]
                    SA_TW["test_writer"]
                    SA_CD["coder"]
                    SA_RV["reviewer"]
                    SA_ORC["orchestrator"]
                end
            end
            subgraph MCPContainer["Remote MCP Server Container"]
                RMCP["FastMCP<br/>Streamable HTTP"]
                TM["TaskManager<br/>Async Task Mgmt"]
            end
        end

        subgraph AISvc["AI Services"]
            BRT["Amazon Bedrock Runtime<br/>Claude Model Invocation"]
        end

        subgraph StorageSvc["Storage & Monitoring"]
            S3["Amazon S3<br/>Logs / Artifacts"]
            DDB["Amazon DynamoDB<br/>Task Persistence"]
            CW["Amazon CloudWatch<br/>Logs & Metrics"]
            XRAY["AWS X-Ray<br/>Distributed Tracing"]
        end

        subgraph BuildSvc["Build & Deploy"]
            ECR["Amazon ECR<br/>Container Images"]
            CB["AWS CodeBuild<br/>Image Build"]
            CFN["AWS CloudFormation<br/>Infra Provisioning"]
        end

        subgraph SecuritySvc["Security & Identity"]
            IAM["AWS IAM<br/>Roles & Policies"]
            STS["AWS STS<br/>OIDC Role Assumption"]
        end
    end

    subgraph LocalDev["Local Development"]
        LMCP["Local MCP Server<br/>stdio transport"]
    end

    subgraph ExtSvc["External Services"]
        GH["GitHub<br/>Repositories"]
    end

    %% Remote access flow
    CC -->|"1. OAuth/JWT"| COG
    GA -->|"1. OAuth/JWT"| COG
    CLI -->|"1. OAuth/JWT"| COG
    COG -->|"2. Authorized"| RMCP

    %% Remote MCP to Agent
    RMCP -->|"3. invoke"| EP
    TM -->|"task state"| DDB

    %% Local access flow
    CC -.->|"stdio"| LMCP
    LMCP -->|"invoke"| EP

    %% Internal agent flow
    EP --> AW
    AW --> CSDK
    CSDK --> Subagents
    CSDK -->|"model invoke"| BRT

    %% External service connections
    AW <-->|"git clone / push"| GH
    AW -->|"log upload"| S3
    EP -->|"logs"| CW
    EP -->|"traces"| XRAY

    %% Build & Deploy
    CB -->|"build image"| ECR
    ECR -.->|"deploy image"| SodaContainer
    ECR -.->|"deploy image"| MCPContainer
    CFN -.->|"provision"| DDB

    %% Security
    IAM -.->|"execution role"| SodaContainer
    IAM -.->|"execution role"| MCPContainer
    STS -.->|"OIDC assume role"| GA

    %% Self-recursive invocation
    CSDK -.->|"recursive invoke"| RMCP

    %% Styling - Nodes
    classDef awsOrange fill:#FF9900,stroke:#232F3E,color:#232F3E,font-weight:bold
    classDef awsDark fill:#232F3E,stroke:#FF9900,color:#ffffff
    classDef awsBlue fill:#2196F3,stroke:#232F3E,color:#ffffff,font-weight:bold
    classDef awsPurple fill:#7B42BC,stroke:#232F3E,color:#ffffff,font-weight:bold
    classDef awsRed fill:#DD344C,stroke:#232F3E,color:#ffffff,font-weight:bold
    classDef external fill:#1a7f37,stroke:#1a7f37,color:#ffffff
    classDef client fill:#527FFF,stroke:#232F3E,color:#ffffff
    classDef local fill:#6B7280,stroke:#374151,color:#ffffff

    class COG awsOrange
    class S3,DDB,CW,XRAY awsOrange
    class EP,AW,CSDK,RMCP,TM awsDark
    class SA_SW,SA_TW,SA_CD,SA_RV,SA_ORC awsDark
    class BRT awsBlue
    class ECR,CB,CFN awsPurple
    class IAM,STS awsRed
    class GH external
    class CC,GA,CLI client
    class LMCP local

    %% Styling - Subgraphs (Container backgrounds)
    style SodaContainer fill:#4DA6FF,stroke:#FF9900,color:#ffffff,stroke-width:2px
    style MCPContainer fill:#66B3FF,stroke:#FF9900,color:#ffffff,stroke-width:2px
```


## (5) Soda環境構築の手順
※作成途中です

  - [開発者チュートリアル](docs/guide/tutorial-developer.md) の通り進める
    - 注意点1：Sodaのデプロイ先のAWSリージョンを任意先にする場合、xxxに修正が必要です。
    - 注意点2：SodaのリモートMCPを動作させるにはOAuth/Cognito認証が必要です。
    - 注意点3：Amazon Bedrock AgentCoreにデプロイするエージェントランタイム名（"soda","soda_remote_mcp"）を別名にする場合、xxxに修正が必要です。

## (6) 変更履歴

| 変更日       | 版数  | 変更内容                     | 変更者 |
| ------------ | ----- | ---------------------------- | ------ |
| 2026-02-12   | 0.1  | ・新規作成                     | 松下 |
| 2026-02-13   | 0.2  | ・目次を追加<br>・Sodaのシステム全体構成を追加 | 松下 |
