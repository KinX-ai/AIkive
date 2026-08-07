import asyncio
import subprocess
import cv2
import threading
import time

def run_app(media_path, rtmp_url, api_key, prompt):
    print("[Core] Đang khởi động luồng stream ngầm...")
    asyncio.run(main_loop(media_path, rtmp_url, api_key, prompt))

async def main_loop(media_path, rtmp_url, api_key, prompt):
    # Lệnh FFmpeg đẩy video thô (rawvideo) từ stdin và ghép âm thanh giả (anullsrc) để test
    ffmpeg_cmd = [
        'ffmpeg', '-y', '-re',
        '-f', 'rawvideo', '-vcodec', 'rawvideo', '-pix_fmt', 'bgr24',
        '-s', '1280x720', '-r', '30', '-i', '-', # Video Input từ pipe Python
        '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=mono', # Audio câm giả lập
        '-c:v', 'libx264', '-preset', 'ultrafast', '-b:v', '2500k',
        '-g', '60', '-keyint_min', '60', '-sc_threshold', '0', # Sửa lỗi "Tốc độ khung hình chính" (Keyframe mỗi 2 giây)
        '-c:a', 'aac', '-ar', '44100', '-b:a', '128k',
        '-f', 'flv', rtmp_url
    ]
    
    process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)
    cap = cv2.VideoCapture(media_path)
    
    print("[Core] FFmpeg đã chạy. Đang nạp frame liên tục lên:", rtmp_url)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            # Hết video thì lặp lại từ đầu
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = cap.read()
            if not ret: break
            
        frame = cv2.resize(frame, (1280, 720))
        
        try:
            # Đẩy byte thô vào stdin của FFmpeg
            process.stdin.write(frame.tobytes())
        except Exception as e:
            print("[Core] Lỗi đường ống FFmpeg:", e)
            break
            
        # Nghỉ 0.033s = ~30 FPS
        await asyncio.sleep(0.033)
