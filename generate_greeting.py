import asyncio
import json
from pathlib import Path
from api_server.config import BASE_DIR
from api_server.server import get_tts

async def main():
    greeting_text = "Xin chào anh chị em là trợ lý ảo của Beenavi em có thể giúp gì cho anh chị ạ"
    tts_inst = get_tts()
    
    if not tts_inst or not tts_inst.enabled:
        print("TTS is not enabled.")
        return
        
    print(f"Bắt đầu ghi âm câu chào: {greeting_text}")
    sentences = tts_inst.split_into_sentences(greeting_text)
    chunks = []
    
    for idx, s in enumerate(sentences):
        clean_s = s.strip()
        if clean_s:
            print(f"Đang sinh âm thanh cho: '{clean_s}'")
            # Tùy thuộc vào việc TTS là class gì, synthesize_sentence_base64 có thể không async (như gọi to_thread)
            # Nếu nó là hàm đồng bộ, ta dùng asyncio.to_thread hoặc chạy trực tiếp
            try:
                audio_b64 = tts_inst.synthesize_sentence_base64(clean_s, None)
                if audio_b64:
                    chunks.append({
                        "audio": audio_b64,
                        "text": clean_s,
                        "index": idx
                    })
            except Exception as e:
                print(f"Lỗi: {e}")

    if chunks:
        cache_data = {
            "text": greeting_text,
            "chunks": chunks
        }
        
        cache_path = BASE_DIR / "ai_engine" / "greeting_cache.json"
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False)
            
        print(f"Đã tạo thành công {cache_path} với {len(chunks)} chunks.")
    else:
        print("Lỗi: Không tạo được chunks nào.")

if __name__ == "__main__":
    asyncio.run(main())
