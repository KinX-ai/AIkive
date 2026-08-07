import asyncio
import subprocess
import cv2
import threading
import time
import os
import queue
import ai_voice

global_chat_queue = queue.Queue()

def run_app(media_path, rtmp_url, api_key, prompt):
    print("[Core] Đang khởi động luồng stream ngầm...")
    asyncio.run(main_loop(media_path, rtmp_url, api_key, prompt))

async def fetch_dummy_comments(q_text):
    # ponytail: Quét liên tục hàng đợi từ giao diện Web UI đẩy xuống
    while True:
        if not global_chat_queue.empty():
            c = global_chat_queue.get()
            await q_text.put(c)
        await asyncio.sleep(0.5)

async def audio_writer_task(q_audio, pipe_path):
    # Mở pipe trên thread riêng
    f = await asyncio.to_thread(open, pipe_path, 'wb')
    
    # 24000 Hz, 16-bit mono = 48000 bytes/giây. 1 frame (1/30s) = 1600 bytes
    silence = b'\x00' * 1600
    
    while True:
        try:
            # Chờ âm thanh từ Gemini (timeout bằng đúng tốc độ 1 frame)
            chunk = await asyncio.wait_for(q_audio.get(), timeout=0.033)
        except asyncio.TimeoutError:
            # Nếu Gemini im lặng, bơm tiếng câm (silence) để FFmpeg không bị tắc hình
            chunk = silence
            
        await asyncio.to_thread(f.write, chunk)
        await asyncio.to_thread(f.flush)

async def main_loop(media_path, rtmp_url, api_key, prompt):
    q_text = asyncio.Queue()
    q_audio = asyncio.Queue()
    
    # Tạo ống nước ảo (Named Pipe) cho âm thanh trên Colab/Linux
    audio_pipe = "audio_fifo.raw"
    if os.path.exists(audio_pipe):
        os.remove(audio_pipe)
    os.mkfifo(audio_pipe)
    
    # Lệnh FFmpeg: Hút video từ stdin (-i -), hút tiếng từ audio_fifo (-i audio_fifo.raw)
    ffmpeg_cmd = [
        'ffmpeg', '-y', '-re',
        '-f', 'rawvideo', '-vcodec', 'rawvideo', '-pix_fmt', 'bgr24',
        '-s', '1280x720', '-r', '30', '-i', '-', 
        '-f', 's16le', '-ar', '24000', '-ac', '1', '-i', audio_pipe, # Gemini xuất 24kHz
        '-c:v', 'libx264', '-preset', 'ultrafast', '-b:v', '2500k',
        '-g', '60', '-keyint_min', '60', '-sc_threshold', '0', 
        '-c:a', 'aac', '-ar', '44100', '-b:a', '128k',
        '-f', 'flv', rtmp_url
    ]
    
    process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)
    cap = cv2.VideoCapture(media_path)
    
    # Kích hoạt não AI và loa (Chạy nền)
    asyncio.create_task(fetch_dummy_comments(q_text))
    asyncio.create_task(ai_voice.gemini_voice_loop(api_key, prompt, q_text, q_audio))
    asyncio.create_task(audio_writer_task(q_audio, audio_pipe))
    
    print("[Core] FFmpeg đã chạy. Nạp frame lên:", rtmp_url)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = cap.read()
            if not ret: break
            
        frame = cv2.resize(frame, (1280, 720))
        
        try:
            process.stdin.write(frame.tobytes())
        except Exception as e:
            print("[Core] Lỗi đường ống FFmpeg:", e)
            break
            
        await asyncio.sleep(0.033)
