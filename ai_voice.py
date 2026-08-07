import asyncio
from google import genai
from google.genai import types

async def gemini_voice_loop(api_key, sys_prompt, q_text, q_audio):
    client = genai.Client(api_key=api_key)
    
    # Cấu hình Gemini trả về Âm thanh (AUDIO)
    config = types.LiveConnectConfig(
        response_modalities=[types.LiveModality.AUDIO],
        system_instruction=types.Content(parts=[types.Part.from_text(text=sys_prompt)])
    )
    
    print("[Gemini] Đã khởi tạo cấu hình AI.")
    while True:
        text = await q_text.get() # Đợi có comment
        print(f"[Gemini] Đang trả lời: {text}")
        
        try:
            # Kết nối Live API (Websocket)
            async with client.aio.live.connect(model="gemini-2.0-flash-exp", config=config) as session:
                await session.send(input=text, end_of_turn=True)
                
                async for response in session.receive():
                    server_content = response.server_content
                    if server_content is not None:
                        model_turn = server_content.model_turn
                        if model_turn is not None:
                            for part in model_turn.parts:
                                if part.inline_data and part.inline_data.data:
                                    # Trả về chunk PCM byte thô (Gemini thường xuất 24kHz PCM)
                                    # Đẩy vào hàng đợi để FFmpeg hoặc Wav2Lip xài
                                    await q_audio.put(part.inline_data.data)
        except Exception as e:
            print("[Gemini] Lỗi kết nối API:", e)
