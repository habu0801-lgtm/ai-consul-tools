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

## 現在の状態：開発済み・運用は停止

**動作しますが、現在は使っていません。** 自分用に作ったものの、運用に乗りませんでした。

理由を正直に書いておきます。

このツールを使うときの流れは、結局「**会議を録音して、PCにファイルを移して、投げる**」でした。
そして同じことは、録音ファイルをそのままNotebookLMに投げても成立します。

- **工数がほとんど変わらない**（どちらもファイルを1回投げるだけ）
- **要約の精度に、劇的な差が出なかった**

自作した分の手間を回収できるほどの差がなかった、というのが結論です。
**既製サービスで足りるなら、自作したものでも使わない**という判断をしました。

技術的には完成しており、セットアップすれば動きます。
同じ構成（Whisper文字起こし → LLM要約 → Chatへ自動投稿）を別の用途で組みたい場合の参考にはなるはずです。

### 作った当時に想定していた拡張（未着手）

- 複数ファイルの一括処理への対応
- Streamlit Cloudへのデプロイ

---

[Shiroji公式サイト](https://shiroji.jp/) ・ [支援内容・料金](https://shiroji.jp/#price) ・ [業務改善の無料相談](https://shiroji.jp/#contact)
