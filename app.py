import streamlit as st
import whisper
from moviepy.video.io.VideoFileClip import VideoFileClip
import os
from datetime import timedelta

model = whisper.load_model("base")

def is_video_file(filename):
    """ファイルが動画かどうかを判定"""
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
    return any(filename.lower().endswith(ext) for ext in video_extensions)

def video_to_audio(video_path):
    """動画から音声を抽出"""
    video = VideoFileClip(video_path)
    audio_path = video_path.replace(os.path.splitext(video_path)[1], '.wav')
    video.audio.write_audiofile(audio_path)
    return audio_path

def generate_srt(segments, speaker_name=""):
    """Whisperの結果をSRT形式に変換"""
    srt_content = ""
    for i, segment in enumerate(segments):
        start = str(timedelta(seconds=segment['start']))
        end = str(timedelta(seconds=segment['end']))
        text = segment['text'].strip()
        
        # 話者名を追加
        if speaker_name:
            text = f"[{speaker_name}] {text}"
        
        srt_content += f"{i+1}\n"
        srt_content += f"{start} --> {end}\n"
        srt_content += f"{text}\n\n"
    
    return srt_content

def parse_srt_time(time_str):
    """SRT時間形式を秒に変換"""
    time_str = time_str.replace(',', '.')
    h, m, s = time_str.split(':')
    return int(h) * 3600 + int(m) * 60 + float(s)

def merge_srt_files(srt_contents):
    """複数のSRTファイルを時間軸で統合"""
    all_segments = []
    
    for srt_content in srt_contents:
        lines = srt_content.strip().split('\n')
        i = 0
        while i < len(lines):
            if lines[i].strip().isdigit():
                # 番号行
                if i + 2 < len(lines):
                    time_line = lines[i + 1]
                    text_line = lines[i + 2]
                    
                    # 時間を解析
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
    
    # 開始時間でソート
    all_segments.sort(key=lambda x: x['start'])
    
    # 統合されたSRTを生成
    merged_srt = ""
    for i, segment in enumerate(all_segments):
        start = str(timedelta(seconds=segment['start']))
        end = str(timedelta(seconds=segment['end']))
        text = segment['text']
        
        merged_srt += f"{i+1}\n"
        merged_srt += f"{start} --> {end}\n"
        merged_srt += f"{text}\n\n"
    
    return merged_srt

st.title("複数音声ファイル → 個別SRT → 統合SRT")

uploaded_files = st.file_uploader(
    "複数の音声/動画ファイルをアップロード", 
    type=["mp4", "avi", "mov", "mkv", "webm", "mp3", "wav", "m4a", "aac", "flac"], 
    accept_multiple_files=True
)

if uploaded_files:
    os.makedirs('uploads', exist_ok=True)
    
    st.write("### ステップ1: 各ファイルからSRT生成中...")
    
    srt_contents = []
    individual_srts = {}
    
    for idx, uploaded_file in enumerate(uploaded_files):
        st.write(f"処理中: {uploaded_file.name}")
        
        # ファイルを保存
        file_path = f"uploads/{uploaded_file.name}"
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # 動画の場合は音声を抽出
        if is_video_file(uploaded_file.name):
            audio_path = video_to_audio(file_path)
        else:
            audio_path = file_path
        
        # 音声認識
        result = model.transcribe(audio_path, language='ja')
        
        # 話者名を設定（ファイル名から）
        speaker_name = f"Speaker_{idx+1}"
        
        # SRT生成
        srt_content = generate_srt(result['segments'], speaker_name)
        srt_contents.append(srt_content)
        individual_srts[uploaded_file.name] = srt_content
        
        # 一時ファイル削除
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(audio_path) and audio_path != file_path:
            os.remove(audio_path)
    
    st.write("### ステップ2: 個別SRTファイル")
    
    # 個別SRTファイルのダウンロードボタン
    for filename, srt_content in individual_srts.items():
        st.download_button(
            label=f"{filename} のSRTをダウンロード",
            data=srt_content,
            file_name=f"{os.path.splitext(filename)[0]}.srt",
            mime="text/plain"
        )
    
    st.write("### ステップ3: SRTファイル統合")
    
    # SRTファイルを統合
    merged_srt = merge_srt_files(srt_contents)
    
    # 統合されたSRTファイルのダウンロードボタン
    st.download_button(
        label="統合されたSRTファイルをダウンロード",
        data=merged_srt,
        file_name="merged_subtitles.srt",
        mime="text/plain"
    )
    
    st.success("処理完了！")