# ai-consul-tools

AIコンサルタント・土生が実際に構築・運用しているAI活用ツール集です。
中小企業・個人事業主向けに、業務効率化を目的としたツールをまとめています。

すべて自分の業務、またはクライアント案件で実際に動かしたものです。
うまくいった構成だけでなく、**途中で設計を変えた理由や踏んだ地雷**も各READMEに残しています。

## ツール一覧

### 業務自動化

#### 📝 meeting-bot

会議音声を自動で文字起こし・要約し、Google Chatに投稿するツール。

- Whisper（OpenAI）で文字起こし
- Claude AIで議事録・要約を生成
- Google Chat Webhookで自動投稿
- 処理済みファイルを自動アーカイブ

詳細は [meeting-bot/README.md](meeting-bot/README.md) を参照。

#### 📅 shift-scheduler

スタッフの希望休・イベント対応日をもとに、月間シフト案を自動生成するStreamlitアプリ。

- 専用UIで条件を入力するだけで下書きを自動生成（手作業90分→約30分に短縮）
- 勤務回数の公平性に配慮した割当ロジック
- CSV出力対応

詳細は [shift-scheduler/README.md](shift-scheduler/README.md) を参照。

#### 📊 kpi-reporter

店舗の週次売上データを自動集計し、サマリーレポートを生成・自動送信するGoogle Apps Scriptツール。

- スタッフ別・項目別の内訳を自動算出
- 時間主導型トリガーで週次自動実行
- 集計履歴をスプレッドシート上に蓄積

詳細は [kpi-reporter/README.md](kpi-reporter/README.md) を参照。

#### 📱 sales-report-form

現場スタッフがその場でスマホから接客実績を入力できる、Google Apps Script製の実績報告フォーム。

- サーバー側でスタッフ名・獲得項目をホワイトリスト検証し、不正入力を防止
- 同時送信の競合をLockServiceで防止、報告者を自動記録
- kpi-reporterと組み合わせて「入力→蓄積→週次集計→自動送信」を一気通貫で自動化

詳細は [sales-report-form/README.md](sales-report-form/README.md) を参照。

### 情報収集・リサーチ

#### 🔍 research-agent

Web・YouTube・Wikipedia・Reddit・トレンドの5エージェントが並列で調査し、GPTが自動でサブクエリを生成して深掘りするマルチエージェント調査ツール。

- 5エージェント並列実行 ＋ 2ラウンド調査（Round 1の結果からサブクエリを自動生成）
- 記事のスニペットではなく本文を全文取得して読む
- 有料APIへの依存を意図的に排除（Google Custom Search → DuckDuckGo、X API → Reddit公開JSON への切替経緯を記載）
- CLI版・チャット版・Slack風Webアプリの3UI

詳細は [research-agent/README.md](research-agent/README.md) を参照。

#### 📰 ai-news-line-bot

AI業界の最新情報を複数の信頼できるソースから自動収集し、日本語に翻訳してLINEに毎朝配信するGoogle Apps Scriptツール。

- OpenAI・Google DeepMind公式ブログ、Hacker News、Reddit、ITmedia AI+、Ledge.aiなど10ソースを横断収集
- 英語タイトルは自動で日本語に翻訳
- RSS/Atom両対応の共通パーサー、レート制限・一時的な取得失敗へのリトライ機構を実装
- 時間主導型トリガーで毎朝7:00(JST)に自動実行

詳細は [ai-news-line-bot/README.md](ai-news-line-bot/README.md) を参照。

#### 🎙️ local-transcriber

音声ファイルをMac上で完結して文字起こしするスクリプト（faster-whisper）。

- クラウドに音声を上げずに、タイムコード付き／なしの2種類を出力
- 38.4分の音声を50.3分で処理（Intel Mac・CPU実行）
- 「要約サービスは淡々と語られた事実を落とす」ことを実測で確認したため、原文を手元に残す用途で作成

詳細は [local-transcriber/README.md](local-transcriber/README.md) を参照。

### 制作・登壇支援

#### 🖼️ slide-generator

構成メモをJSONで渡すだけで、ブランドデザインが統一されたPPTXスライドを自動生成するNode.js製ジェネレーター。

- 7種類のスライドタイプに対応（目次・セクション・2カラム・表・まとめ等）
- `brand` フィールドの差し替えで企業向け・コンサル用途にも転用可能
- 文字量と余白に応じたフォントサイズ自動計算

詳細は [slide-generator/README.md](slide-generator/README.md) を参照。

#### 🎬 video-production

Claude Codeのスキルスタック（video-use + HyperFrames）を使った、会話ベースの動画制作・編集。

**実例：くらし×AI活用の会 第4回告知動画**
- 20秒のInstagramストーリー用縦型動画（1080×1920px）を実制作
- 実写合成 / カラーグレード / シーン間トランジション / テキストアニメーション / BGM自動選定
- 公式チェック全項目クリア・納品完了（2026年8月2日）

詳細は [video-production/README.md](video-production/README.md) を参照。

#### 🎯 presentation-extensions

講座・登壇のために自作したChrome拡張2種（Manifest V3）。

- **Laser Pointer**：画面共有中にPowerPoint風のレーザーポインター演出。iframe内のスライドでも動作
- **Lecture Timer**：講座・作業セッション用カウントダウンタイマー。フルスクリーン表示対応
- 外部通信なし、権限は必要最小限

詳細は [presentation-extensions/README.md](presentation-extensions/README.md) を参照。

### 公開Webサイト

#### 🗺️ tokyo-art-events

東京都内の美術館の展覧会情報を自動収集し、地図付きで一覧できる公開Webサイト。

- 13館の展覧会情報を毎日自動収集（GitHub Actions）
- Google Mapsで全館の場所・開催状況を確認可能
- 開催状況フィルタ・検索に対応

公開サイト: https://tokyo-art-events.vercel.app
詳細は [tokyo-art-events/README.md](tokyo-art-events/README.md) を参照。

### クライアント案件（事例紹介）

> 以下はクライアント様の業務データ・店舗情報を含むため、**設計の記録のみ**を公開しています。
> ソース・実物ファイルは含みません。

#### 🧮 cost-management-tool

飲食店向けの食材原価管理ツール（スプレッドシート5シート構成 ＋ GAS連携）。

- 仕入れ単価を更新すると、原価率・目標との差・適正販売価格・値上げアラートが自動再計算
- Googleフォームからのスマホ入力で、伝票入力→原価率更新までを一気通貫
- 「値上げすべきか」の判断を1分以内にできる状態を実現
- v1→v8で潰した8つの設計上の問題（IFERRORで捕まらないバグ、最新単価を行順で判定していた構造欠陥など）を記録

詳細は [cost-management-tool/README.md](cost-management-tool/README.md) を参照。

#### 🌐 landing-page

店舗集客用ランディングページの制作事例。

- ブランドガイドラインがない状態から、公式SNSの実投稿を参照して世界観を再現
- 正式な予約URL未確定でも導線を殺さない暫定設計
- 依存なしの単一HTMLで、ホスティング先を選ばない構成

詳細は [landing-page/README.md](landing-page/README.md) を参照。

## 今後追加予定

- **sns-copy-generator**：商品写真からSNS投稿文を自動生成
- **video-series**：複数シーン動画の自動編集テンプレート

## 対象

- 会議録作成・共有に時間がかかっている方
- シフト作成・売上集計など定型業務に時間を取られている方
- AIを業務に取り入れたいが何から始めればいいかわからない方
- 小規模チームで効率化を進めたい経営者・管理職の方

## 作者

Masahiro Habu - AIコンサルタント
