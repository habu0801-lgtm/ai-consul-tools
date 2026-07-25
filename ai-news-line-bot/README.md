# AI最新情報 LINE自動配信bot — セットアップ手順

`Code.gs` と `appsscript.json` を新規のGoogle Apps Scriptプロジェクトに貼り付けて使う。

## 1. GASプロジェクトを作成する

1. https://script.google.com で新規プロジェクトを作成
2. デフォルトの `コード.gs` の中身を、このフォルダの `Code.gs` の内容で置き換える
3. 左メニューの「プロジェクトの設定」→「`appsscript.json` マニフェストファイルをエディタで表示する」にチェック
4. `appsscript.json` タブが出るので、このフォルダの `appsscript.json` の内容で置き換える

## 2. LINE公式アカウント（Messaging API）を作る

1. https://developers.line.biz/console/ にアクセスし、LINEアカウントでログイン
2. 新規プロバイダーを作成（名前は何でもよい、例: 個人用）
3. 「Messaging API」のチャンネルを新規作成（チャンネル名・説明・業種などを入力）
4. 作成したチャンネルの「Messaging API設定」タブを開く
5. 「チャネルアクセストークン（長期）」を発行し、コピーしておく

## 3. Script Propertiesにトークンを設定する

1. GASエディタの「プロジェクトの設定」→「スクリプト プロパティ」
2. `LINE_CHANNEL_ACCESS_TOKEN` を追加し、手順2-5でコピーしたトークンを貼り付け

## 4. 自分のLINE User IDを取得する

当初はGASをWebhook受け口としてデプロイする方式を試したが、GASのWebアプリはPOSTリクエストに必ず302リダイレクトを返す仕様があり、LINEの Webhook配信はこれを追従しないため失敗することが判明した（curlで直接検証済み）。代わりに、Webhook不要の「友だち一覧取得API」を使う。

1. 事前に、LINE Developersの「Messaging API設定」タブのQRコードから、自分のLINEでこの公式アカウントを友だち追加しておく
2. GASエディタで関数選択を `getFollowerIds` にして実行
3. 実行ログに `200 {"userIds":["Uxxxxxxxxxxxx..."]}` のような形で出るので、その `U` から始まる文字列をコピー
4. 「プロジェクトの設定」→「スクリプト プロパティ」に `LINE_USER_ID` として追加

このbotはメッセージを送るだけ（Push API）で、LINE側からのメッセージ受信は使わないので、LINE Developersの「Webhookを使用する」はオフに戻しておいてよい。GASのWeb Appデプロイも今回は不要だったので、削除してしまって問題ない（デプロイを管理→アーカイブアイコン）。

## 5. 動作確認

1. GASエディタで関数選択を `testFetchAll` にして実行 → 実行ログに各ソースの新着タイトルが出ることを確認
2. 関数選択を `main` にして実行 → 自分のLINEにその日の新着ダイジェストが届くことを確認
3. 関数選択を `setupTrigger` にして実行 → 毎朝7:00(JST)の自動実行トリガーが設定される（実行ログに「トリガーを作成しました」と出る）

以降は毎朝7時に自動でLINEに届く。配信時刻を変えたい場合は `Code.gs` 内の `setupTrigger()` の `atHour(7)` を書き換えて再実行する。

## 参考: 情報源リスト

- OpenAI Blog（公式）
- Google DeepMind Blog（公式）
- TestingCatalog（海外まとめ・リーク情報）
- Hacker News（AI関連キーワードで絞り込み）
- Reddit r/OpenAI, r/ClaudeAI, r/singularity, r/artificial
- ITmedia AI+（日本語ニュース）
- Ledge.ai（日本語ニュース、有志の非公式フィード経由）

Anthropic公式・Every.to・著名な個人Xアカウントは、公式RSSがない/API制約があるため今回は対象外。将来的に追加したくなったら相談してほしい。
