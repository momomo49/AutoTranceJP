import streamlit as st
import whisper
from moviepy.editor import AudioFileClip
import os
from datetime import timedelta
import subprocess

model = whisper.load_model("base")

def compress_audio_ffmpeg(input_path, output_path, target_bitrate="64k"):
    """
    ffmpegで音声ファイルを圧縮
    input_path: 元の音声ファイル
    output_path: 圧縮後のファイル
    target_bitrate: 目標ビットレート（例: "64k"）
    """
    command = [
        "ffmpeg",
        "-y",  # 上書き
        "-i", input_path,
        "-b:a", target_bitrate,
        output_path
    ]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg error: {result.stderr.decode()}")
    return output_path

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
        
        # ファイルサイズを確認
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        
        # ファイルサイズが200MBを超える場合は圧縮
        if file_size_mb > 200:
            st.write(f"{uploaded_file.name} はファイルサイズが大きいため、ffmpegで圧縮します")
            compressed_path = file_path.replace(os.path.splitext(file_path)[1], "_compressed.mp3")
            try:
                compress_audio_ffmpeg(file_path, compressed_path, target_bitrate="64k")
                audio_path = compressed_path
            except Exception as e:
                st.error(f"ffmpeg 圧縮エラー: {e}")
                continue
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