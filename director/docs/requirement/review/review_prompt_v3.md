# 命令
以下の成果物を、指定されたレビュー観点に基づいて評価してください。  
指摘箇所と指摘内容が一目で分かる形式で、Markdownレポートとして出力してください。  
成果物は以下のディレクトリにあります：  
/home/ubuntu/work/Director/docs/requirement/mcp_tool/github_projects_mcp.py
/home/ubuntu/work/Director/docs/requirement/mcp_tool/requirements.txt
/home/ubuntu/work/Director/docs/requirement/prompt/DirectorAgentPrompt.md
/home/ubuntu/work/Director/docs/requirement/SystemTest/VAD_System_Test_Scenario.md
/home/ubuntu/work/Director/docs/requirement/01_はじめに.md
/home/ubuntu/work/Director/docs/requirement/02_DirectorAgentの概要.md
/home/ubuntu/work/Director/docs/requirement/03_機能要件.md
/home/ubuntu/work/Director/docs/requirement/04_非機能要件.md
/home/ubuntu/work/Director/docs/requirement/05_エージェント間インターフェース.md
/home/ubuntu/work/Director/docs/requirement/06_シーケンス図.md
/home/ubuntu/work/Director/sample/directoragent_run.md
/home/ubuntu/work/Director/docs/requirement/issue_template/template.md
/home/ubuntu/work/Director/docs/requirement/IntegrationTest/integration_test_spec.md

# 文脈
あなたはソフトウェア成果物の上級Reviewerです。  
このレビューは、ソフトウェア開発をAIエージェントにより全自動化し、生産性を向上させるプロジェクトの一環です。  

関連資料として以下を参照できます：  
- マルチエージェントシステム構成図  
  ・/home/ubuntu/review-work/マルチエージェントシステム構成図1.png  
  ・/home/ubuntu/review-work/マルチエージェントシステム構成図2.png  

DirectorAgentの要件定義・設計書を作成し、GitHubMCPServerを開発し、EC2上でDirectoreAgentの動作確認を行いました。

これまでのレビューレポートは以下のディレクトリにあります：  
/home/ubuntu/review-work/review_report_v1.md
/home/ubuntu/review-work/review_report_v2.md
/home/ubuntu/review-work/review_report_v3.md

# レビュー観点
1. **可読性**
   - typoがないこと
   - 複雑な文章構成となっていないこと
   - 一般的でない表現が使用されていないこと
   - 冗長な表現がないこと
   - 「はじめに」が基本的な内容を短時間で理解できるようにまとまっていること
   - 図表に見切れやずれがないこと
   - 文体（だ・である調／です・ます調）の統一
   - 箇条書きの句点の統一（体言止めの場合は句点不要、文章の場合は句点あり）

2. **整合性**
   - ドキュメント間の整合性が取れていること
   - 不要な重複記載がないこと
   - 改善経緯は記載せず、最新内容のみ記載されていること
   - 参考文献や参照先のリンクが埋め込まれていること
   - 目次や内部リンクのリンク切れがないこと

3. **妥当性**
   - フォルダ名・ファイル名・タイトル・章節見出しが内容を端的に示していること
   - フォルダ構成が妥当であること
   - フローチャートのmermaid記法は許容（GitHub上の成果物がマスタとなるため）

4. **暫定検討箇所の注意書き**
   - 暫定的な検討箇所には変更発生の可能性があることが注意書きとして明記されていること

# 出力フォーマット（Markdown）
- 1ファイルにまとめる
- 成果物別に章を分ける
- 資料の上から下に向けて順に修正できるように並べる
