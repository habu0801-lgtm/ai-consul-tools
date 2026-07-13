# ai-consul-tools

実際に構築・運用しているAI活用ツール集です。
中小企業・個人事業主向けに、業務効率化を目的としたツールをまとめています。

## ツール一覧

### 📝 meeting-bot

会議音声を自動で文字起こし・要約し、Google Chatに投稿するツール。

- Whisper（OpenAI）で文字起こし
- Claude AIで議事録・要約を生成
- Google Chat Webhookで自動投稿
- 処理済みファイルを自動アーカイブ

詳細は [meeting-bot/README.md](meeting-bot/README.md) を参照。

### 📅 shift-scheduler

スタッフの希望休・イベント対応日をもとに、月間シフト案を自動生成するStreamlitアプリ。

- 専用UIで条件を入力するだけで下書きを自動生成（手作業90分→約30分に短縮）
- 勤務回数の公平性に配慮した割当ロジック
- CSV出力対応

詳細は [shift-scheduler/README.md](shift-scheduler/README.md) を参照。

### 📊 kpi-reporter

店舗の週次売上データを自動集計し、サマリーレポートを生成・自動送信するGoogle Apps Scriptツール。

- スタッフ別・項目別の内訳を自動算出
- 時間主導型トリガーで週次自動実行
- 集計履歴をスプレッドシート上に蓄積

詳細は [kpi-reporter/README.md](kpi-reporter/README.md) を参照。

### 📱 sales-report-form

現場スタッフがその場でスマホから接客実績を入力できる、Google Apps Script製の実績報告フォーム。

- サーバー側でスタッフ名・獲得項目をホワイトリスト検証し、不正入力を防止
- 同時送信の競合をLockServiceで防止、報告者を自動記録
- kpi-reporterと組み合わせて「入力→蓄積→週次集計→自動送信」を一気通貫で自動化

詳細は [sales-report-form/README.md](sales-report-form/README.md) を参照。

### 🗺️ tokyo-art-events

東京都内の美術館の展覧会情報を自動収集し、地図付きで一覧できる公開Webサイト。

- 13館の展覧会情報を毎日自動収集（GitHub Actions）
- Google Mapsで全館の場所・開催状況を確認可能
- 開催状況フィルタ・検索に対応

公開サイト: https://tokyo-art-events.vercel.app
詳細は [tokyo-art-events/README.md](tokyo-art-events/README.md) を参照。

## 対象

- 会議録作成・共有に時間がかかっている方
- シフト作成・売上集計など定型業務に時間を取られている方
- AIを業務に取り入れたいが何から始めればいいかわからない方
- 小規模チームで効率化を進めたい経営者・管理職の方

## 作者

Masahiro Habu - AIコンサルタント
