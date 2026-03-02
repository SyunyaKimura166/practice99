# dotfiles

個人の設定ファイルを管理するリポジトリ。

## 構成

```
claude-code/
├── settings.json       # Claude Code 設定 (Opus)
└── settings.eco.json   # Claude Code 設定 (Sonnet / エコモード)
```

## セットアップ

```bash
# Claude Code 設定を配置
cp claude-code/settings.json ~/.claude/settings.json
```

エコモード（Sonnet ベース）を使う場合:

```bash
cp claude-code/settings.eco.json ~/.claude/settings.json
```
