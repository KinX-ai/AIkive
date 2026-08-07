import gradio as gr
import threading
import time
import downloader

# Giả lập import core logic
# from livestream_core import main_stream_logic

def start_livestream(media_file, rtmp_url, api_key, prompt):
    if not media_file or not rtmp_url or not api_key:
        return "Lỗi: Thiếu file mẫu, RTMP hoặc API Key!"
    
    yield "Đang tải modules (Wav2Lip, Models)... Lần đầu có thể mất 2-3 phút."
    downloader.setup_all()
    
    yield f"Tải xong! Đang khởi động stream... \nFile: {media_file}\nĐích: {rtmp_url}"
    
    # ponytail: Lưu file media_file, set biến môi trường, gọi livestream_core.py chạy ngầm
    # threading.Thread(target=main_stream_logic, args=(media_file, rtmp_url, api_key, prompt)).start()

def stop_livestream():
    # ponytail: Kill thread/subprocess FFmpeg
    return "Đã dừng."

with gr.Blocks(title="AI Livestream Control Panel") as ui:
    gr.Markdown("## 🔴 Bảng điều khiển AI Livestream")
    
    with gr.Row():
        with gr.Column():
            media_in = gr.File(label="Upload Video/Ảnh mẫu (.mp4, .png)", file_types=["image", "video"])
            prompt_in = gr.Textbox(label="Tính cách AI (System Prompt)", value="Bạn là một streamer vui tính. Trả lời comment ngắn gọn.", lines=3)
        
        with gr.Column():
            api_key_in = gr.Textbox(label="Gemini API Key", type="password")
            rtmp_in = gr.Textbox(label="RTMP URL + Key (VD: rtmp://a.rtmp.youtube.com/live2/KEY)")
            
            with gr.Row():
                btn_start = gr.Button("▶ Bắt đầu Stream", variant="primary")
                btn_stop = gr.Button("⏹ Dừng", variant="stop")
                
    status_out = gr.Textbox(label="Trạng thái hệ thống", interactive=False)

    btn_start.click(fn=start_livestream, inputs=[media_in, rtmp_in, api_key_in, prompt_in], outputs=status_out)
    btn_stop.click(fn=stop_livestream, inputs=[], outputs=status_out)

if __name__ == "__main__":
    # share=True để Colab tự tạo public link (xyz.gradio.live)
    ui.launch(share=True, debug=True)
