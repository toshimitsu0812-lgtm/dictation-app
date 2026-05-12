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

st.set_page_config(page_title="Dictation Generator", page_icon="🎧")

st.title("Dictation Generator (Edge TTS)")
st.write("各文の前に『No.X』と読み上げ、1秒おいて英文を流し、最後に10秒の間隔を空けます。")

# 設定オプション
with st.sidebar:
    st.header("Settings")
    voice_option = st.selectbox(
        "音声を選択してください",
        ["en-US-AvaNeural", "en-US-GuyNeural", "en-GB-SoniaNeural", "en-AU-WilliamNeural"],
        index=0
    )
    speed = st.slider("読み上げ速度 (%)", -20, 20, 0, step=5)
    rate = f"{speed:+d}%"

# 10個の入力欄
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
            # 非同期処理を実行するためのループ
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                for i, text in enumerate(texts):
                    if text.strip():
                        # 1. "Number X" の読み上げを作成
                        label_text = f"Number {i+1}"
                        label_bytes = loop.run_until_complete(generate_edge_audio(label_text, voice_option))
                        label_audio = AudioSegment.from_file(io.BytesIO(label_bytes), format="mp3")
                        
                        # 2. 本文の読み上げを作成
                        # 設定した速度(rate)を反映
                        communicate = edge_tts.Communicate(text, voice_option, rate=rate)
                        audio_bytes = b""
                        async def get_main_audio():
                            nonlocal audio_bytes
                            async for chunk in communicate.stream():
                                if chunk["type"] == "audio":
                                    audio_bytes += chunk["data"]
                        loop.run_until_complete(get_main_audio())
                        
                        sentence_audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")
                        
                        # 3. 結合: [No.X] + [1秒] + [本文] + [10秒]
                        combined_audio += label_audio + one_sec_silence + sentence_audio + ten_sec_silence

                # 最終出力をバッファに保存
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
