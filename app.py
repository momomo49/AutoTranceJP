import streamlit as st
import whisper
import moviepy.editor as mp
import os
from datetime import timedelta

model = whisper.load_model("base")

def is_video_file(filename):
    """ファイルが動画かどうかを判定"""
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
    audio_extensions = ['.mp3', '.wav', '.m4a', '.aac', '.flac']
    return any(filename.lower().endswith(ext) for ext in video_extensions)

def video_to_audio(video_path):
    """動画から音声を抽出"""
    video = mp.VideoFileClip(video_path)
    audio_path = video_path.replace(os.path.splitext(video_path)[1], '.wav')
    video.audio.write_audiofile(audio_path)
    return audio_path

def generate_srt(segments):
    """Whisperの結果をSRT形式に変換"""
    srt_content = ""
    for i, segment in enumerate(segments):
        start = str(timedelta(seconds=segment['start']))
        end = str(timedelta(seconds=segment['end']))
        text = segment['text'].strip()
        
        srt_content += f"{i+1}\n"
        srt_content += f"{start} --> {end}\n"
        srt_content += f"{text}\n\n"
    
    return srt_content

st.title("日本語音声認識 SRT生成")

uploaded_file = st.file_uploader("動画または音声をアップロード", type=["mp4", "avi", "mov", "mkv", "webm", "mp3", "wav", "m4a", "aac", "flac"])

if uploaded_file is not None:
    # ファイルを保存
    file_path = f"uploads/{uploaded_file.name}"
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    if is_video_file(uploaded_file.name):
        # 動画ファイルの場合、音声を抽出
        audio_path = video_to_audio(file_path)
    else:
        # 音声ファイルの場合、そのまま使用
        audio_path = file_path
    
    # 音声認識
    result = model.transcribe(audio_path, language='ja')
    
    # SRT生成
    srt_content = generate_srt(result['segments'])
    
    # SRTファイル保存
    srt_path = file_path.replace(os.path.splitext(uploaded_file.name)[1], '.srt')
    with open(srt_path, 'w', encoding='utf-8') as f:
        f.write(srt_content)
    
    # ダウンロードボタン
    with open(srt_path, "rb") as f:
        st.download_button(
            label="SRTファイルをダウンロード",
            data=f,
            file_name=os.path.basename(srt_path),
            mime="text/vtt",
        )

    # 一時ファイルの削除
    os.remove(file_path)
    os.remove(srt_path)