# presentation-extensions

講座・登壇のために自作したChrome拡張2種（Manifest V3）。
オンライン・対面どちらでも、ブラウザ画面を使って進行するときの困りごとを解消するために作りました。

## 🔴 laser-pointer

ブラウザ画面共有中に、PowerPointのレーザーポインターのような演出ができる拡張機能。

- 任意のページ上にオーバーレイを描画（content script）
- 全フレーム対応（`all_frames: true`）なので、iframe内のスライドでも動く
- 設定はポップアップUIから変更、`chrome.storage` に保存
- 権限は `activeTab` と `storage` のみ

### 使い方

1. Chromeで `chrome://extensions` を開く
2. 「デベロッパーモード」をON
3. 「パッケージ化されていない拡張機能を読み込む」→ `laser-pointer/` を選択
4. ツールバーのアイコンからON/OFF

## ⏱️ lecture-timer

講座・作業セッション用のカウントダウンタイマー拡張機能。

- ポップアップ表示とフルスクリーン表示の2モード（`fullscreen.html`）
- `chrome.alarms` でバックグラウンド計測。タブを切り替えてもズレない
- 終了時に通知（`notifications` 権限）
- 権限は `storage` / `alarms` / `notifications` のみ

### 使い方

`lecture-timer/` を同じ手順で読み込みます。
ワークの時間を投影しておきたいときは、フルスクリーン表示を別ウィンドウで開いて画面共有すると使いやすいです。

## 技術

Chrome拡張 Manifest V3 / content script / service worker / chrome.storage / chrome.alarms。
外部通信は一切していません。

## 状態

どちらも基本機能は実装済み。実際の講座で使いながら調整中です。
