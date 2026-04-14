#!/usr/bin/env python3
"""Whisperで文字起こしし、GPT-4o-miniで要約してGoogle Chatへ投稿する。"""

import json
import os
import sys
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional, Tuple

import requests
from dotenv import load_dotenv
from openai import OpenAI

SUMMARY_MODEL = "gpt-4o-mini"
load_dotenv(override=True)


def resolve_audio_path(arg_path: str) -> Path:
    candidate = Path(arg_path).expanduser()
    if not candidate.is_absolute():
        candidate = (Path.cwd() / candidate).resolve()

    if candidate.is_file():
        return candidate

    nfd_candidate = Path(unicodedata.normalize("NFD", str(candidate)))
    if nfd_candidate.is_file():
        return nfd_candidate

    sys.exit(f"音声ファイルが見つかりません: {candidate}")


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        sys.exit(f"環境変数 {name} が設定されていません。")
    return value


def transcribe_audio(audio_path: Path) -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    with open(audio_path, "rb") as f:
        audio_bytes = f.read()
    response = requests.post(
        "https://api.openai.com/v1/audio/transcriptions",
        headers={"Authorization": f"Bearer {api_key}"},
        files={"file": ("audio.m4a", audio_bytes, "audio/mp4")},
        data={"model": "whisper-1"},
    )
    return response.json()["text"]


def parse_meeting_info_from_filename(
    audio_path: Path,
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    stem = audio_path.stem
    parts = stem.split("_")

    meeting_date = None
    meeting_title = None
    participants = None

    if len(parts) >= 1 and len(parts[0]) == 8 and parts[0].isdigit():
        meeting_date = f"{parts[0][0:4]}/{parts[0][4:6]}/{parts[0][6:8]}"
    if len(parts) >= 2 and parts[1].strip():
        meeting_title = parts[1].strip()
    if len(parts) >= 3:
        participants_text = "_".join(parts[2:]).strip()
        if participants_text:
            participants = participants_text

    return meeting_date, meeting_title, participants


def fill_missing_meeting_info(
    meeting_date: Optional[str], meeting_title: Optional[str], participants: Optional[str]
) -> Tuple[str, str, str]:
    if not meeting_date:
        meeting_date = input("日時を入力してください（例: 2026/04/14）：").strip()
    if not meeting_title:
        meeting_title = input("会議名を入力してください：").strip()
    if not participants:
        participants = input("参加者を入力してください：").strip()

    return meeting_date, meeting_title, participants


def summarize_with_gpt(
    transcript_text: str, meeting_date: str, meeting_title: str, participants: str
) -> str:
    prompt = (
        "あなたは優秀なエグゼクティブ・アシスタントです。\n"
        "以下の【会議の文字起こしデータ】を読み込み、指定された【出力フォーマット】に従って、論理的で分かりやすい議事録を作成してください。\n\n"
        "# 事前情報（ファイル名から取得）\n"
        f"- 日時: {meeting_date}\n"
        f"- 会議名: {meeting_title}\n"
        f"- 参加者: {participants}\n\n"
        "# 指示およびルール\n"
        "1. 文字起こしのノイズ（えー、あの、などのフィラー）や雑談は除外して、要点のみを抽出してください。\n"
        "2. 発言の単なる書き起こし（会話形式）ではなく、第三者が読んでも「何が決まったか」「次に誰が何をするか」がわかるように要約・構造化してください。\n"
        "3. 会話の文脈から、[会議の目的]や[アジェンダ]を推測して整理してください。\n"
        "4. [決定事項]と[Next Action]は最も重要です。必ず抽出してください。Next Actionは「誰が」「何を」「いつまでに」やるのかを明確に箇条書きにしてください。明言されていない場合は「要確認」としてください。\n"
        "5. 結論に至った理由や、対立した意見、懸念点などの[議論の過程]も、箇条書きで簡潔にまとめてください。\n"
        "6. 出力はMarkdown形式で行ってください。\n\n"
        "# 出力フォーマット\n"
        "## 【会議名】（※内容から適切なタイトルを推測してください）\n"
        "* **日時：** （※わかる範囲で記載）\n"
        "* **参加者：** （※会話に出てくる登場人物を記載）\n"
        "* **会議の目的・ゴール：**\n\n"
        "## 1. 決定事項【最重要】\n"
        "* （箇条書きで簡潔に）\n\n"
        "## 2. Next Action（タスク）【最重要】\n"
        "* [担当者名]：[タスク内容]（期限：[いつまで]）\n\n"
        "## 3. アジェンダと議論の過程\n"
        "### アジェンダ1：（議題名）\n"
        "* **背景・前提：**\n"
        "* **主な議論・懸念点：**\n\n"
        "## 4. 保留事項・次回持ち越し\n"
        "* （今回決まらなかったこと、次回までの宿題など）\n\n"
        f"--- 文字起こし ---\n{transcript_text}\n"
    )
    client = OpenAI()
    try:
        response = client.chat.completions.create(
            model=SUMMARY_MODEL,
            temperature=0.2,
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception as exc:
        sys.exit(f"OpenAI 要約API呼び出しに失敗しました: {exc}")

    summary = (response.choices[0].message.content or "").strip()
    if not summary:
        sys.exit("OpenAI APIの応答から要約テキストを取得できませんでした。")
    return summary


def post_to_google_chat(summary_text: str, webhook_url: str) -> None:
    payload = {"text": summary_text}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json; charset=UTF-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as response:
            status = response.getcode()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        sys.exit(f"Google Chat投稿に失敗しました: HTTP {exc.code} {detail}")
    except urllib.error.URLError as exc:
        sys.exit(f"Google Chatへの接続に失敗しました: {exc}")

    if status < 200 or status >= 300:
        sys.exit(f"Google Chat投稿に失敗しました: HTTP {status}")


def main() -> None:
    require_env("OPENAI_API_KEY")
    webhook_url = require_env("GOOGLE_CHAT_WEBHOOK")

    if len(sys.argv) != 2:
        sys.exit("使い方: python3 transcribe.py <音声ファイルパス>")

    audio_path = resolve_audio_path(sys.argv[1])
    meeting_date, meeting_title, participants = parse_meeting_info_from_filename(audio_path)
    meeting_date, meeting_title, participants = fill_missing_meeting_info(
        meeting_date, meeting_title, participants
    )

    transcript_text = transcribe_audio(audio_path)
    summary_text = summarize_with_gpt(transcript_text, meeting_date, meeting_title, participants)
    post_to_google_chat(summary_text, webhook_url)

    print("=== 文字起こし結果 ===")
    print(transcript_text)
    print("\n=== 要約結果 ===")
    print(summary_text)
    print("\nGoogle Chat への投稿が完了しました。")


if __name__ == "__main__":
    main()
