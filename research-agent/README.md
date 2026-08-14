# research-agent

Web・YouTube・Wikipedia・Reddit・トレンドの **5エージェントが並列でリサーチ**し、
GPTが自動でサブクエリを生成して深掘り、最後に総合インサイトをまとめるマルチエージェント調査ツール。

「〇〇について調べて」の一言で、複数の情報源を横断した調査レポートが出てくる状態を目指して作りました。

## 特徴

- **5エージェント並列実行**（ThreadPoolExecutor）で、1ソースが遅くても全体が止まらない
- **2ラウンド調査**：Round 1の結果をGPTが読んで自動でサブクエリを生成 → Round 2でWeb深掘り
- **記事本文の全文取得**：検索結果のスニペットだけでなく、BeautifulSoupで本文まで読む
- **日本語クエリの自動英訳**（Reddit調査用）
- **APIキーなしでも動く情報源を優先**（下記「設計上の判断」参照）
- CLI版・チャット版・Slack風WebアプリのUIを3種類用意

## エージェント構成

| エージェント | データソース | APIキー |
|---|---|---|
| 🌐 Web調査員 | DuckDuckGo検索 ＋ 記事全文スクレイピング | 不要 |
| 📺 YouTube調査員 | YouTube Data API | 必要 |
| 📖 Wikipedia調査員 | Wikipedia API | 不要 |
| 📱 Reddit調査員 | Reddit公開JSON（日本語クエリは自動英訳） | 不要 |
| 📈 トレンド調査員 | Google Trends RSS ＋ サジェスト | 不要 |

総合インサイトの生成にOpenAI APIキーを使います。

## 設計上の判断（つまずいた所と回避策）

実運用に乗せるまでに、外部APIの制約で3回設計を変えています。

| 当初の想定 | 起きた問題 | 最終的な選択 |
|---|---|---|
| Google Custom Search API | 検索エンジンID発行＋Cloud課金設定が必要。403が解消できず | **DuckDuckGo検索**（キー不要・無制限） |
| Twitter/Instagram API | X APIが月$100〜に値上げされ、個人利用では非現実的 | **Reddit公開JSON**（キー不要・無料） |
| pytrendsで直接Google Trends | 429（レート制限）が頻発 | **RSSフィード方式**に切替えて安定化 |

「動く構成にたどり着くこと」を優先し、有料APIへの依存を意図的に減らしています。

### 名残について

このツールは元々「飲食店のAI活用事例」を調べる**専用ツール**として着手し、後からクエリ固定部分を外して
汎用化しました。そのため `main.py` のレポート見出しや各スクリプトのデフォルトクエリに
「飲食店」という初期スコープの名残が残っています（クエリを明示的に渡せば任意のテーマを調査できます）。
実運用は `research_quick.py` に寄せているため、そちらを入口として使ってください。

## 使い方

### セットアップ

```bash
pip install -r requirements.txt
cp .env.example .env  # OPENAI_API_KEY と YOUTUBE_API_KEY を記入
```

### CLI（高速版・Claude Codeから呼ぶ想定）

```bash
python research_quick.py "調査したいクエリ"
```

結果のJSONが `outputs/` に保存され、読みやすいテキストサマリーが標準出力に出ます。

### チャット版

```bash
python chat_research.py
```

### Slack風Webアプリ

```bash
python app.py
```

→ http://localhost:5000

## ファイル構成

```
research-agent/
├── research_quick.py   高速CLI版（Claude Code連携用の入口）
├── chat_research.py    対話型チャット版
├── app.py              Flask製のSlack風Webアプリ
├── main.py             基本の実行スクリプト
├── config.py           APIキー・タイムアウト・プロンプト定義
├── agents/             5エージェントの実装（base_agent.pyを継承）
├── utils/              APIクライアント・ロガー
├── templates/          WebアプリのHTML
└── tests/              エージェントのテスト
```

## 環境変数

`.env.example` を `.env` にコピーして記入してください。
`OPENAI_API_KEY`（インサイト生成）と `YOUTUBE_API_KEY`（YouTube調査）以外は任意です。

## 状態

運用中。Claude Codeのスラッシュコマンドから呼び出して日常的に使っています。
