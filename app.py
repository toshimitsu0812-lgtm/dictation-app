import streamlit as st
import asyncio
import edge_tts
from pydub import AudioSegment
import io

# Edge TTSから音声を一括で取得する関数（エラーを避けるためシンプルにしました）
async def get_audio_payload(text, voice, rate="+0%"):
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

st.set_page_config(page_title="Dictation Generator", page_icon="🎧")

st.title("Dictation Generator (Edge TTS)")
st.write("各文の前に『Number X』と読み上げ、1秒おいて英文を流し、最後に10秒の間隔を空けます。")

with st.sidebar:
    st.header("Settings")
    voice_option = st.selectbox(
        "音声を選択してください",
        ["en-US-AvaNeural", "en-US-GuyNeural", "en-GB-SoniaNeural", "en-AU-WilliamNeural"],
        index=0
    )
    speed = st.slider("読み上げ速度 (%)", -20, 20, 0, step=5)
    rate_str = f"{speed:+d}%"

texts = []
for i in range(10):
    t = st.text_input(f"Sentence {i+1}", key=f"t_{i}", placeholder=f"Ex: This is sentence number {i+1}.")
    texts.append(t)

if st.button("音声ファイルを作成", type="primary"):
    if not any(t.strip() for t in texts):
        st.error("少なくとも1つの文章を入力してください。")
    else:
        combined_audio = AudioSegment.empty()
        one_sec_silence = AudioSegment.silent(duration=1000)   # 1秒の無音
        ten_sec_silence = AudioSegment.silent(duration=10000) # 10秒の無音

        with st.spinner("高品質な音声を生成して結合しています..."):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                for i, text in enumerate(texts):
                    if text.strip():
                        # 1. "Number X" の音声を生成
                        label_text = f"Number {i+1}"
                        label_bytes = loop.run_until_complete(get_audio_payload(label_text, voice_option))
                        label_audio = AudioSegment.from_file(io.BytesIO(label_bytes), format="mp3")
                        
                        # 2. 本文の音声を生成
                        sentence_bytes = loop.run_until_complete(get_audio_payload(text, voice_option, rate=rate_str))
                        sentence_audio = AudioSegment.from_file(io.BytesIO(sentence_bytes), format="mp3")
                        
                        # 3. 結合: [Number X] + [1秒] + [本文] + [10秒]
                        combined_audio += label_audio + one_sec_silence + sentence_audio + ten_sec_silence

                out_buffer = io.BytesIO()
                combined_audio.export(out_buffer, format="mp3")
                
                st.audio(out_buffer)
                st.download_button(
                    label="音声をダウンロード (MP3)",
                    data=out_buffer.getvalue(),
                    file_name="dictation_material.mp3",
                    mime="audio/mp3"
                )
                st.success("作成が完了しました！")
                
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
                st.info("Pythonのバージョンが3.11または3.12であることを確認してください。")
