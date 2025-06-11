import streamlit as st
import whisper
import os
from datetime import timedelta

# SRT生成関数
def generate_srt(segments, speaker_name=""):
    srt_content = ""
    for i, segment in enumerate(segments):
        start = str(timedelta(seconds=segment['start']))
        end = str(timedelta(seconds=segment['end']))
        text = segment['text'].strip()
        if speaker_name:
            text = f"[{speaker_name}] {text}"
        srt_content += f"{i+1}\n"
        srt_content += f"{start} --> {end}\n"
        srt_content += f"{text}\n\n"
    return srt_content

# SRT統合関数
def parse_srt_time(time_str):
    time_str = time_str.replace(',', '.')
    h, m, s = time_str.split(':')
    return int(h) * 3600 + int(m) * 60 + float(s)

def merge_srt_files(srt_contents):
    all_segments = []
    for srt_content in srt_contents:
        lines = srt_content.strip().split('\n')
        i = 0
        while i < len(lines):
            if lines[i].strip().isdigit():
                if i + 2 < len(lines):
                    time_line = lines[i + 1]
                    text_line = lines[i + 2]
                    start_str, end_str = time_line.split(' --> ')
                    start_time = parse_srt_time(start_str.strip())
                    end_time = parse_srt_time(end_str.strip())
                    all_segments.append({
                        'start': start_time,
                        'end': end_time,
                        'text': text_line.strip()
                    })
                    i += 3
                else:
                    i += 1
            else:
                i += 1
    all_segments.sort(key=lambda x: x['start'])
    merged_srt = ""
    for i, segment in enumerate(all_segments):
        start = str(timedelta(seconds=segment['start']))
        end = str(timedelta(seconds=segment['end']))
        text = segment['text']
        merged_srt += f"{i+1}\n"
        merged_srt += f"{start} --> {end}\n"
        merged_srt += f"{text}\n\n"
    return merged_srt

# セッションステートでSRTとファイル名を保持
if "srt_list" not in st.session_state:
    st.session_state.srt_list = []
if "file_names" not in st.session_state:
    st.session_state.file_names = []
if "done_files" not in st.session_state:
    st.session_state.done_files = []

st.title("1ファイルずつアップロード→SRT統合")

uploaded_file = st.file_uploader(
    "音声/動画ファイルをアップロード",
    type=["mp3", "wav", "m4a", "aac", "flac", "mp4", "avi", "mov", "mkv", "webm"]
)

if uploaded_file is not None:
    os.makedirs('uploads', exist_ok=True)
    file_path = f"uploads/{uploaded_file.name}"
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    model = whisper.load_model("base")
    result = model.transcribe(file_path, language='ja')
    srt_content = generate_srt(result['segments'], speaker_name=uploaded_file.name)
    st.session_state.srt_list.append(srt_content)
    st.session_state.file_names.append(uploaded_file.name)
    st.session_state.done_files.append(uploaded_file.name)
    st.success(f"{uploaded_file.name} のSRTを保存しました！")
    os.remove(file_path)

# 保存済みSRTのリスト表示と個別ダウンロード
if st.session_state.file_names:
    st.write("保存済みSRTファイル：")
    for name, srt_content in zip(st.session_state.file_names, st.session_state.srt_list):
        st.download_button(
            label=f"{name} のSRTをダウンロード",
            data=srt_content.encode("utf-8"),
            file_name=f"{os.path.splitext(name)[0]}.srt",
            mime="text/plain"
        )

# 統合ボタン
if st.button("保存済みSRTを統合してダウンロード"):
    merged_srt = merge_srt_files(st.session_state.srt_list)
    st.download_button(
        label="統合SRTをダウンロード",
        data=merged_srt.encode("utf-8"),
        file_name="merged_subtitles.srt",
        mime="text/plain"
    )

# リセットボタン
if st.button("リセット（全てのSRTを削除）"):
    st.session_state.srt_list = []
    st.session_state.file_names = []
    st.success("保存済みSRTをリセットしました！")