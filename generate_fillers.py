import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import asyncio
import json
from pathlib import Path
from api_server.config import BASE_DIR
from ai_engine.text_to_speech import TTSManager

def generate_all_fillers():
    print("[Fillers] Khoi tao TTSManager tren CPU...", flush=True)
    tts_inst = TTSManager()
    tts_inst.device_setting = "cpu"  # Dung CPU de khong dung cham VRAM cua server dang chay
    if not tts_inst.enabled:
        print("TTS khong kha dung.", flush=True)
        return

    fillers = [
        {"id": "filler_hello", "text": "Em chào anh chị, em là trợ lý ảo của BeeNavi, sau đây em sẽ tư vấn cho anh chị."},
        {"id": "filler_wait_1", "text": "Dạ vâng ạ, anh chị đợi em một chút nhé."},
        {"id": "filler_wait_2", "text": "Em đã nhận yêu cầu, đang tra cứu cho anh chị đây ạ."},
        {"id": "filler_wait_3", "text": "Dạ, để em kiểm tra thông tin ngay cho anh chị nhé."},
        {"id": "filler_wait_4", "text": "Vâng ạ, anh chị chờ em trong giây lát nhé."},
        {"id": "filler_wait_5", "text": "Dạ vâng, em đang chuẩn bị thông tin cho mình đây ạ."},
        {"id": "filler_unclear", "text": "Dạ em chưa nghe rõ, anh chị có thể nói lại hoặc gõ tin nhắn giúp em nhé."}
    ]
    fillers_dir = BASE_DIR / "ai_engine" / "fillers"
    fillers_dir.mkdir(parents=True, exist_ok=True)

    manifest = []
    for item in fillers:
        print(f"Sinh audio tren CPU: [{item['id']}] {item['text']}", flush=True)
        audio_b64 = tts_inst.synthesize_sentence_base64(item['text'], None)
        if audio_b64:
            file_path = fillers_dir / f"{item['id']}.json"
            data = {"id": item['id'], "text": item['text'], "audio": audio_b64}
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
            manifest.append(data)
            print(f"  -> Da luu {file_path}", flush=True)

    # Lưu file tổng hợp
    summary_path = BASE_DIR / "ai_engine" / "fillers_manifest.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False)
    print(f"-> Hoan tat tao {len(manifest)} cau dem tai {summary_path}", flush=True)

if __name__ == "__main__":
    generate_all_fillers()
