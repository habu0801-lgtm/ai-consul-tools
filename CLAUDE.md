# meeting-bot プロジェクト概要

## このツールの目的
会議音声ファイル（.m4a / .mp4）を自動で文字起こし・要約し、
議事録をGoogle Chatに自動投稿するツール。

## リポジトリ
- GitHub: https://github.com/habu0801-lgtm/ai-consul-tools
- ローカル: ~/meeting-bot/

## ファイル構成
```
~/meeting-bot/
├── app.py          Streamlit UI（アップロード・確認・投稿）
├── transcribe.py   文字起こし・要約・Google Chat投稿のコアロジック
├── watch.py        フォルダ監視による完全自動化
├── .env            APIキー（Gitに含めない）
└── meeting-bot/    サブディレクトリ（READMEなど）
```

## 技術スタック
- **文字起こし**: OpenAI Whisper API
- **要約・議事録生成**: Claude AI（または GPT）
- **投稿先**: Google Chat Webhook
- **UI**: Streamlit
- **自動化**: watch.py でフォルダ監視→自動処理

## 使い方（2パターン）
### 手動（Streamlit UI）
```bash
cd ~/meeting-bot
streamlit run app.py
```
→ ブラウザで音声ファイルをアップロードして処理

### 自動（フォルダ監視）
```bash
python watch.py
```
→ 音声ファイルを所定フォルダに入れると自動処理・投稿

## 環境変数（.env）
```
OPENAI_API_KEY=xxx
GOOGLE_CHAT_WEBHOOK_URL=xxx
```

## 開発ルール
- APIキーは必ず .env 経由で管理（Gitに含めない）
- 音声ファイル（.m4a, .mp4）は .gitignore で除外済み
- Python 3.11（/usr/local/bin/python3.11）を使用

## 現状・課題
- 基本機能は完成・運用中
- Streamlit Cloud へのデプロイは未実施
- 複数ファイルの一括処理は未対応
