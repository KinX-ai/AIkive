import asyncio
import tempfile
import subprocess
import numpy as np
import scipy.io.wavfile as wavfile
import os
from google import genai
from google.genai import types

async def gemini_voice_loop(api_key, sys_prompt, q_text, q_video_files, q_audio_bytes, base_media_path, voice_name):
    client = genai.Client(api_key=api_key)
    config = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        system_instruction=types.Content(parts=[types.Part.from_text(text=sys_prompt)]),
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name=voice_name
                )
            )
        )
    )
    
    print("[Gemini] Đã khởi tạo não AI.")
    while True:
        text = await q_text.get()
        print(f"[Gemini] Đang suy nghĩ: {text}")
        
        full_audio = bytearray()
        try:
            async with client.aio.live.connect(model="gemini-3.1-flash-live-preview", config=config) as session:
                await session.send(input=text, end_of_turn=True)
                async for response in session.receive():
                    if response.server_content and response.server_content.model_turn:
                        for part in response.server_content.model_turn.parts:
                            if part.inline_data and part.inline_data.data:
                                full_audio.extend(part.inline_data.data)
        except Exception as e:
            print("[Gemini] Lỗi API:", e)
            continue
            
        if len(full_audio) > 0:
            print(f"[Wav2Lip] Bắt đầu gọt miệng cho audio dài {len(full_audio)} bytes...")
            
            # 1. Lưu PCM ra file WAV
            audio_np = np.frombuffer(full_audio, dtype=np.int16)
            tmp_wav = tempfile.mktemp(suffix=".wav")
            wavfile.write(tmp_wav, 24000, audio_np)
            
            # 2. Chạy Wav2Lip render nhép miệng
            tmp_mp4 = tempfile.mktemp(suffix=".mp4")
            cmd = [
                "python", "Wav2Lip/inference.py",
                "--checkpoint_path", "Wav2Lip/checkpoints/wav2lip_gan.pth",
                "--face", base_media_path,
                "--audio", tmp_wav,
                "--outfile", tmp_mp4,
                "--nosmooth" # Tắt smooth để render lẹ
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            print("[Wav2Lip] Gọt miệng xong! Đẩy lên Facebook.")
            
            # 3. Quăng video và audio vào hàng đợi cho luồng phát xơi
            q_video_files.put_nowait(tmp_mp4)
            q_audio_bytes.put_nowait(full_audio)
            
            try:
                os.remove(tmp_wav)
            except: pass
