＃命令
DirectorAgentの要件定義書を作成してください。

＃文脈
ソフトウェア開発をAIエージェントにより全自動化させ生産性を向上させるプロジェクトの一環です。

DirectorAgentについては
・/home/ubuntu/work/Director/DirectorAgentの位置づけ1.png
・/home/ubuntu/work/Director/DirectorAgentの位置づけ2.png
を参照してください。

DirectorAgentでは主に下記を実現する必要があります。
・ユーザや他Agentから登録されたissueの一覧を取得する（issueの種別は下記9つ）
　 - 新規開発（New Development）
　 - 機能追加（Feature）
　 - 不具合修正（Bug）
　 - リファクタ（Refactor）
　 - 調査/分析（Research）
　 - パフォーマンス改善（Perf）
　 - セキュリティ（Security）
　 - ドキュメント（Docs）
　 - PoC / プロトタイプ（Proof of Concept）
・下記の観点などから最も優先度の高いissueを選択し、projects上のステータスをBacklogからReadyに変更
　 - 顧客からの要求
　 - ユーザの不満
　 - 自社プロダクトと市場のニーズを踏まえ、マーケティング上一番効果の高いもの
　 - 既存機能改善
　 - 不具合修正
　 - リファクタリング（構造、振る舞い）
・Readyに変更する際に、DevPlannerAgentsと不具合分析Agentsのどちらに対応させるか依頼先を選定し、タグを変更する
・DirectorAgentの実行契機は、Phase1では人による実行、Phase2ではAgentによる総合的な判断（他Agentの現在のタスク実行状況や過去に同規模の要求を実行した際の時間から予測される時間、タスクの優先度など）となります。

＃出力フォーマット
以下のフォルダに含まれる内容をフォーマットとしてください
/home/ubuntu/work/practice2/調査_サブエージェント
    ├── 01_はじめに.md
    ├── 02_Claudeサブエージェントの作成と対話型実行.md
    ├── 03_GitHubActionsでサブエージェント使用.md
    ├── 04_ClaudeAgentSDKでサブエージェント使用.md
    ├── 05_プロセス分割のサブエージェント.md
    ├── examples
    │   └── agents.py
    ├── images
    │   ├── 画像1.png
    │   ├── 画像10.png
    │   ├── 画像11.png
    │   ├── 画像12.png
    │   ├── 画像13.png
    │   ├── 画像14.png
    │   ├── 画像15.png
    │   ├── 画像16.png
    │   ├── 画像17.png
    │   ├── 画像2.png
    │   ├── 画像3.png
    │   ├── 画像4.png
    │   ├── 画像5.png
    │   ├── 画像6.png
    │   ├── 画像7.png
    │   ├── 画像8.png
    │   └── 画像9.png
    └── src
        ├── agents.py
        ├── get_iovpf_repos.py
        ├── sample.py
        ├── sub_agent_example.py
        └── subproccess_subagents
            ├── log.txt
            └── subproccess_subagents.py

#具体例
出力フォーマットには従っていませんが、要件定義書の内容の具体例は下記を参考にしてください
/home/ubuntu/work/DevOps/docs/requirement/要件定義_cicd_pipeline_agent.md
