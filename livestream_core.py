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
    while True:
        if not global_chat_queue.empty():
            c = global_chat_queue.get()
            await q_text.put(c)
        await asyncio.sleep(0.5)

def audio_writer_thread(q_audio_bytes, pipe_path):
    f = open(pipe_path, 'wb')
    silence = b'\x00' * 1600
    while True:
        try:
            chunk = q_audio_bytes.get(timeout=0.033)
            f.write(chunk)
            f.flush()
        except queue.Empty:
            f.write(silence)
            f.flush()

def video_writer_task(process, media_path, base_frame, q_video_files):
    current_cap = cv2.VideoCapture(media_path)
    is_playing_ai = False
    ai_mp4_path = ""
    
    while True:
        # Nếu có video nhép miệng mới từ AI, ưu tiên đổi sang video AI
        if not is_playing_ai and not q_video_files.empty():
            ai_mp4_path = q_video_files.get()
            current_cap.release()
            current_cap = cv2.VideoCapture(ai_mp4_path)
            is_playing_ai = True
            
        ret, frame = current_cap.read()
        
        # Nếu hết video
        if not ret:
            current_cap.release()
            if is_playing_ai:
                # Nếu video AI chạy xong, vứt đi, quay về ảnh mẫu gốc
                is_playing_ai = False
                try: os.remove(ai_mp4_path)
                except: pass
                current_cap = cv2.VideoCapture(media_path)
            else:
                # Nếu video mẫu gốc chạy xong, lặp lại từ đầu
                current_cap = cv2.VideoCapture(media_path)
            
            ret, frame = current_cap.read()
            if not ret: frame = base_frame
            
        frame = cv2.resize(frame, (1280, 720))
        try:
            process.stdin.write(frame.tobytes())
        except Exception:
            break
        time.sleep(0.033)

async def main_loop(media_path, rtmp_url, api_key, prompt):
    q_text = asyncio.Queue()
    q_video_files = queue.Queue()
    q_audio_bytes = queue.Queue()
    
    audio_pipe = "audio_fifo.raw"
    if os.path.exists(audio_pipe):
        os.remove(audio_pipe)
    os.mkfifo(audio_pipe)
    
    ffmpeg_cmd = [
        'ffmpeg', '-y', '-re',
        '-f', 'rawvideo', '-vcodec', 'rawvideo', '-pix_fmt', 'bgr24',
        '-s', '1280x720', '-r', '30', '-i', '-', 
        '-f', 's16le', '-ar', '24000', '-ac', '1', '-i', audio_pipe, 
        '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-preset', 'ultrafast', '-b:v', '2500k',
        '-g', '60', '-keyint_min', '60', '-sc_threshold', '0', 
        '-c:a', 'aac', '-ar', '44100', '-b:a', '128k',
        '-f', 'flv', rtmp_url
    ]
    
    process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)
    
    cap = cv2.VideoCapture(media_path)
    ret, base_frame = cap.read()
    if not ret:
        base_frame = cv2.imread(media_path)
    cap.release()
            
    asyncio.create_task(fetch_dummy_comments(q_text))
    # Nạp cơ miệng
    asyncio.create_task(ai_voice.gemini_voice_loop(api_key, prompt, q_text, q_video_files, q_audio_bytes, media_path))
    
    # 2 Luồng Bơm Hình và Tiếng song song
    threading.Thread(target=audio_writer_thread, args=(q_audio_bytes, audio_pipe), daemon=True).start()
    threading.Thread(target=video_writer_task, args=(process, media_path, base_frame, q_video_files), daemon=True).start()
    
    print("[Core] HỆ THỐNG ĐÃ LÊN SÓNG:", rtmp_url)
    while True:
        await asyncio.sleep(1)
