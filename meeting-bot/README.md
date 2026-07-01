# meeting-bot

会議音声を自動で文字起こし・要約し、Google Chatに投稿するツールです。

## できること

1. 音声ファイル（.m4a / .mp4）を入れる
2. ターミナルでコマンドを実行する、またはStreamlit UIから操作する
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
pip install requests python-dotenv openai watchdog streamlit
```

### 3. .envファイルを作成する

```bash
cp .env.example .env
```

`.env` をテキストエディタで開いて以下を入力：

```
OPENAI_API_KEY=あなたのOpenAI APIキー
GOOGLE_CHAT_WEBHOOK=あなたのGoogle Chat Webhook URL
```

## 使い方（2パターン）

### A. 自動（フォルダ監視）

```bash
python watch.py
```

起動している間、このmeeting-botフォルダに音声ファイル（.m4a / .mp4）を入れると、自動で文字起こし→要約→Google Chatへの投稿までを行います。処理済みファイルはprocessed/フォルダへ自動的に移動されます。

### B. 手動（Streamlit UI）

```bash
streamlit run app.py
```

ブラウザが開くので、音声ファイルをアップロード→抽出された日時・参加者・タイトルを確認/編集→投稿、という流れで処理できます。

## 今後の拡張案

- 複数ファイルの一括処理への対応
- Streamlit Cloudへのデプロイ
