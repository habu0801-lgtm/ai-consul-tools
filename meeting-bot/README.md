# 議事録自動化ツール（meeting-bot）

## 概要
会議音声を自動で文字起こし・要約してGoogle Chatに投稿するツール

## 使用技術
- OpenAI Whisper API（文字起こし）
- OpenAI GPT-4o-mini（要約）
- Google Chat Webhook（投稿）
- Python 3.11

## セットアップ手順
1. Python 3.11をインストール
2. 必要ライブラリをインストール
3. .envファイルを作成してAPIキーを設定
4. watch.pyを起動

## 使い方
ファイル名のルール：20260414_会議名_参加者.m4a
meeting-botフォルダに音声ファイルを入れるだけで自動処理される

## ファイル構成
- transcribe.py：メインスクリプト
- watch.py：フォルダ監視スクリプト
- .env：APIキー管理（GitHubにはpushしない）

## 対応音声形式
m4a、mp4

## 注意事項
- .envファイルは絶対にGitHubにpushしない
- APIキーは.envで管理する
