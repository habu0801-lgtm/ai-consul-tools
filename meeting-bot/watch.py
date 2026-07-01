#!/usr/bin/env python3
"""meeting-botフォルダを監視し、新規音声/動画ファイルを自動処理する。"""

import shutil
import subprocess
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

WATCH_DIR = Path(__file__).resolve().parent
PROCESSED_DIR = WATCH_DIR / "processed"
TARGET_EXTENSIONS = {".m4a", ".mp4"}
TRANSCRIBE_COMMAND = [sys.executable, "transcribe.py"]
POLL_INTERVAL_SECONDS = 3


def list_target_files() -> set[Path]:
    return {
        path
        for path in WATCH_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in TARGET_EXTENSIONS
    }


def process_file(file_path: Path) -> bool:
    command = TRANSCRIBE_COMMAND + [file_path.name]
    print(f"[INFO] 実行: {' '.join(command)}")
    result = subprocess.run(command, cwd=str(WATCH_DIR))
    if result.returncode != 0:
        print(f"[ERROR] 処理失敗: {file_path.name} (exit_code={result.returncode})")
        return False

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    destination = PROCESSED_DIR / file_path.name
    shutil.move(str(file_path), str(destination))
    print(f"[INFO] 処理済みへ移動: {destination}")
    return True


def main() -> None:
    load_dotenv(WATCH_DIR / ".env", override=True)
    known_files = list_target_files()
    print(f"[INFO] 監視開始: {WATCH_DIR}")

    while True:
        try:
            current_files = list_target_files()
            new_files = sorted(current_files - known_files)
            for file_path in new_files:
                process_file(file_path)
            known_files = current_files
            time.sleep(POLL_INTERVAL_SECONDS)
        except KeyboardInterrupt:
            print("\n[INFO] 監視を終了しました。")
            break


if __name__ == "__main__":
    main()
