import streamlit as st
import subprocess
from pathlib import Path

st.title("会議Bot ダッシュボード")
st.header("音声ファイルをアップロード")
uploaded_file = st.file_uploader("音声ファイルを選択（m4a / mp4）", type=["m4a", "mp4"])

if uploaded_file is not None:
    save_path = Path.home() / "Desktop" / "meeting-bot" / uploaded_file.name
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.success(f"アップロード完了：{uploaded_file.name}")
    st.header("文字起こし・要約・投稿")
    if st.button("処理を実行する"):
        with st.spinner("処理中..."):
            result = subprocess.run(
                ["/usr/local/bin/python3.11", "transcribe.py", str(save_path)],
                cwd=str(Path.home() / "Desktop" / "meeting-bot"),
                capture_output=True,
                text=True
            )
        if result.returncode == 0:
            st.success("処理完了！Google Chatに投稿しました。")
            st.text_area("出力ログ", result.stdout, height=300)
        else:
            st.error("エラーが発生しました")
            st.text_area("エラーログ", result.stderr, height=300)