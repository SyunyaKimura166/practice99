＃命令
GitHubActionsについて下記の観点でまとめた調査結果報告書を作成してください。
・GitHubActionsの動作の実態
・同時並行でのワークフロー実行
・EC2上で使用するClaudeAgentSDKとの違い
・参照するコンテキスト範囲
・GitHubActionsの使用方法

＃文脈
ソフトウェア開発をAIエージェントにより全自動化させ生産性を向上させるプロジェクトの一環です。

一部AgentはEC2でなくGitHubActionsのClaudeCodeを使用したいですが、過去に知見がありません。
よって、過去に知見があるEC2上で使用するClaudeCodeとの違いをまとめた調査結果報告書を作成したいです。

調査結果は
/home/ubuntu/work/Director/docs/research/GitHubActions
に出力してください。

可読性などの観点から必要に応じてファイルを分けて作成してください。

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
出力フォーマットには従っていませんが、内容は下記を参考にしてください
/home/ubuntu/work/Director/docs/research/GitHubActions/create/調査_GitHubActionsの仕様.md
