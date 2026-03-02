＃命令
VADの特徴やVADとAutowareの違いについてまとめた調査結果報告書を作成してください。

＃文脈
ソフトウェア開発をAIエージェントにより全自動化させ生産性を向上させるプロジェクトの一環です。

ソフトウェア開発の題材としてVADを使用しCARLAと連携させたいですが、過去に知見がありません。
よって、過去に知見があるAutowareとCARLAの連携との違いをまとめた調査結果報告書を作成したいです。

VADについては
https://github.com/hustvl/VAD
を参照してください。

Autowareについては
https://github.com/autowarefoundation/autoware
を参照してください。

CARLAについては
https://github.com/carla-simulator/carla
を参照してください

調査結果は
/home/ubuntu/work/Director/docs/research/VAD-Autoware/調査_VADとAutowareの比較.md
に出力してください

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
/home/ubuntu/work/Director/docs/research/VAD-Autoware/create/調査_VADとAutowareの比較.md
