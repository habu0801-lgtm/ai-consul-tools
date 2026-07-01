import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# .envを読み込む（このファイルと同じディレクトリ）
load_dotenv(Path(__file__).resolve().parent / ".env", override=True)

from transcribe import (
    transcribe_audio,
    extract_meeting_info_with_ai,
    get_file_datetime,
    summarize_with_gpt,
    post_to_google_chat,
)

st.title("会議Bot ダッシュボード")

if "stage" not in st.session_state:
    st.session_state.stage = "upload"

if st.session_state.stage == "upload":
    st.header("音声ファイルをアップロード")
    uploaded_file = st.file_uploader("音声ファイルを選択（m4a / mp4）", type=["m4a", "mp4"])

    if uploaded_file is not None:
        if st.button("文字起こし・情報抽出を開始"):
            save_path = Path(__file__).resolve().parent / uploaded_file.name
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            with st.spinner("文字起こし中..."):
                transcript = transcribe_audio(save_path)

            with st.spinner("タイトル・参加者を抽出中..."):
                meeting_title, participants = extract_meeting_info_with_ai(transcript)
                meeting_date = get_file_datetime(save_path)

            st.session_state.transcript = transcript
            st.session_state.meeting_date = meeting_date
            st.session_state.meeting_title = meeting_title
            st.session_state.participants = participants
            st.session_state.audio_path = str(save_path)
            st.session_state.stage = "confirm"
            st.rerun()

elif st.session_state.stage == "confirm":
    st.header("抽出された情報を確認・編集してください")

    meeting_date = st.text_input("日時", value=st.session_state.meeting_date)
    participants = st.text_input("参加者", value=st.session_state.participants)
    meeting_title = st.text_input("タイトル", value=st.session_state.meeting_title)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("この内容で投稿する", type="primary"):
            with st.spinner("議事録を作成中..."):
                summary = summarize_with_gpt(
                    st.session_state.transcript,
                    meeting_date,
                    meeting_title,
                    participants,
                )
            webhook_url = os.environ.get("GOOGLE_CHAT_WEBHOOK")
            post_to_google_chat(summary, webhook_url)
            st.success("Google Chatに投稿しました！")
            st.subheader("議事録")
            st.markdown(summary)
            if st.button("新しいファイルを処理する"):
                st.session_state.stage = "upload"
                st.rerun()

    with col2:
        if st.button("やり直す"):
            st.session_state.stage = "upload"
            st.rerun()
