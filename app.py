import streamlit as st
import asyncio
import edge_tts
from pydub import AudioSegment
import io

# Edge TTSで音声を生成する非同期関数
async def generate_edge_audio(text, voice):
    communicate = edge_tts.Communicate(text, voice)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

st.title("Dictation Generator (Edge TTS)")
st.write("英文を入力して、10秒間隔のディクテーション音源を作成します。")

# 声の選択（アメリカ英語やイギリス英語など選べます）
voice_option = st.selectbox(
    "音声を選択してください",
    ["en-US-GuyNeural", "en-US-AvaNeural", "en-GB-SoniaNeural", "en-AU-WilliamNeural"]
)

texts = []
for i in range(10):
    t = st.text_input(f"Sentence {i+1}", key=f"t_{i}")
    texts.append(t)

if st.button("音声ファイルを作成"):
    combined_audio = AudioSegment.empty()
    silence = AudioSegment.silent(duration=10000)  # 10秒の無音

    with st.spinner("Microsoft Edgeの高品質音声で作成中..."):
        # 非同期処理を実行するためのループ
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        for text in texts:
            if text.strip():
                # Edge TTSから音声バイナリを取得
                audio_bytes = loop.run_until_complete(generate_edge_audio(text, voice_option))
                
                # pydubで扱える形式に変換
                sentence_audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")
                combined_audio += sentence_audio + silence

        # 最終出力をバッファに保存
        out_buffer = io.BytesIO()
        combined_audio.export(out_buffer, format="mp3")
        
        st.audio(out_buffer)
        st.download_button("音声を保存 (MP3)", data=out_buffer.getvalue(), file_name="dictation.mp3")
