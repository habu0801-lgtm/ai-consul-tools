#!/usr/bin/env python3
"""音声ファイルを文字起こしして、タイムコード付き/なしの2種類を書き出す。

使い方:
    ./whisper-env/bin/python transcribe.py <音声ファイル> [出力先ディレクトリ]
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

from faster_whisper import WhisperModel

MODEL_SIZE = "medium"


def format_timestamp(seconds: float) -> str:
    minutes, secs = divmod(int(seconds), 60)
    return f"{minutes:02d}:{secs:02d}"


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    audio_path = Path(sys.argv[1])
    if not audio_path.exists():
        print(f"ファイルが見つかりません: {audio_path}")
        return 1

    out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else audio_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"モデル読み込み中（{MODEL_SIZE}）…初回はダウンロードが走ります", flush=True)
    model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")

    print(f"文字起こし開始: {audio_path.name}", flush=True)
    started = time.time()

    segments, info = model.transcribe(
        str(audio_path),
        language="ja",
        beam_size=5,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 500},
    )

    timed_lines: list[str] = []
    plain_lines: list[str] = []

    for segment in segments:
        text = segment.text.strip()
        if not text:
            continue
        stamp = format_timestamp(segment.start)
        timed_lines.append(f"[{stamp}] {text}")
        plain_lines.append(text)
        elapsed = time.time() - started
        print(f"  {stamp} / 経過 {elapsed / 60:.1f}分 … {text[:40]}", flush=True)

    stem = audio_path.stem
    timed_path = out_dir / f"{stem}_文字起こし_タイムコード付き.txt"
    plain_path = out_dir / f"{stem}_文字起こし.txt"

    timed_path.write_text("\n".join(timed_lines) + "\n", encoding="utf-8")
    plain_path.write_text("\n".join(plain_lines) + "\n", encoding="utf-8")

    total = time.time() - started
    print(f"\n完了（{total / 60:.1f}分・音声長 {info.duration / 60:.1f}分）", flush=True)
    print(f"  {timed_path}", flush=True)
    print(f"  {plain_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
