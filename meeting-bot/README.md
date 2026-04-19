# 🎙️ meeting-bot

会議音声を自動で文字起こし・要約し、Google Chatに投稿するツールです。

## できること

1. 音声ファイル（.m4a / .mp4）を入れる
2. ターミナルでコマンドを実行する
3. 議事録がGoogle Chatに自動投稿される

## 必要なもの

- Mac（またはLinux）
- Python 3.8以上
- OpenAI APIキー（文字起こし・要約に使用）
- Google Chat Webhook URL（投稿先）

## セットアップ手順

### 1. このリポジトリを取得する

```bash
git clone https://github.com/habu0801-lgtm/ai-consul-tools.git
cd ai-consul-tools/meeting-bot
```

### 2. Pythonライブラリをインストールする

```bash
pip install requests python-dotenv openai
```

### 3. .envファイルを作成する

```bash
cp .env.example .env
```

`.env` をテキストエディタで開いて以下を入力：
