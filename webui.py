import gradio as gr
import threading
import time
import downloader
import importlib
import livestream_core
importlib.reload(livestream_core)

def start_livestream(media_file, rtmp_url, stream_key, api_key, prompt, voice_name):
    import importlib
    import livestream_core
    importlib.reload(livestream_core)
    
    if not media_file or not rtmp_url or not stream_key or not api_key:
        yield "Lỗi: Thiếu thông tin cấu hình!", None
        return
    
    full_rtmp = f"{rtmp_url.rstrip('/')}/{stream_key}"
    
    yield "Đang tải modules (Wav2Lip, Models)... Lần đầu có thể mất 2-3 phút.", None
    downloader.setup_all()
    
    yield f"Tải xong! Đang khởi động stream... \nFile: {media_file}\nĐích: {full_rtmp}", None
    
    # Bật luồng stream ngầm
    threading.Thread(target=livestream_core.run_app, args=(media_file, full_rtmp, api_key, prompt, voice_name), daemon=True).start()

def stop_livestream():
    # ponytail: Kill thread/subprocess FFmpeg
    return "Đã dừng."

def send_test_comment(text):
    if text.strip():
        livestream_core.global_chat_queue.put(text)
    return "" # Xoá trắng ô nhập sau khi gửi

with gr.Blocks(title="AI Livestream Control Panel") as ui:
    gr.Markdown("## 🔴 Bảng điều khiển AI Livestream")
    
    with gr.Row():
        with gr.Column():
            media_in = gr.File(label="Upload Video/Ảnh mẫu (.mp4, .png)", file_types=["image", "video"])
            prompt_in = gr.Textbox(label="Tính cách AI (System Prompt)", value="Bạn là một streamer vui tính. Trả lời comment ngắn gọn.", lines=3)
            voice_in = gr.Dropdown(choices=["Puck", "Charon", "Kore", "Fenrir", "Aoede"], value="Aoede", label="Giọng AI cố định")
        
        with gr.Column():
            api_key_in = gr.Textbox(label="Gemini API Key", type="password")
            with gr.Row():
                rtmp_in = gr.Textbox(label="RTMP URL (Server)")
                stream_key_in = gr.Textbox(label="Stream Key (Khóa luồng)", type="password")
            
            with gr.Row():
                btn_start = gr.Button("▶ Bắt đầu Stream", variant="primary")
                btn_stop = gr.Button("⏹ Dừng", variant="stop")
                
    with gr.Row():
        status_out = gr.Textbox(label="Trạng thái hệ thống", interactive=False)
        preview_out = gr.Image(label="Live Preview (Hình trích xuất ngẫu nhiên)", interactive=False)
        
    gr.Markdown("### 💬 Test Tương Tác AI (Chỉ hoạt động khi Stream đang chạy)")
    with gr.Row():
        test_comment_in = gr.Textbox(label="Nhập comment để AI đọc", placeholder="VD: Hôm nay bạn khỏe không?", scale=4)
        btn_send = gr.Button("Gửi cho AI", variant="secondary", scale=1)

    btn_start.click(fn=start_livestream, inputs=[media_in, rtmp_in, stream_key_in, api_key_in, prompt_in, voice_in], outputs=[status_out, preview_out])
    btn_stop.click(fn=stop_livestream, inputs=[], outputs=status_out)
    btn_send.click(fn=send_test_comment, inputs=test_comment_in, outputs=test_comment_in)
    test_comment_in.submit(fn=send_test_comment, inputs=test_comment_in, outputs=test_comment_in)

if __name__ == "__main__":
    # share=True để Colab tự tạo public link (xyz.gradio.live)
    ui.launch(share=True, debug=True)
