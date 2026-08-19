"""
scripts/generate_greeting_cache.py
Script tổng hợp trước (pre-synthesize) câu chào mở đầu của cuộc gọi thoại bằng VieNeu-TTS
và lưu vào ai_engine/greeting_cache.json để phát tức thì (0ms latency).
"""
import base64
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from ai_engine.text_to_speech import TTSManager


def generate_greeting_cache():
    # Câu chào chuẩn không có ký tự đặc biệt, không gạch chéo để VieNeu-TTS phát âm tự nhiên nhất
    greeting_text = "Xin chào anh chị, em là trợ lý ảo của Beenavi. Em có thể giúp gì cho anh chị ạ?"
    
    print("=" * 60)
    print("  ĐANG TỔNG HỢP VÀ GHI ÂM CÂU CHÀO MỞ ĐẦU CUỘC GỌI...")
    print(f"  Nội dung: '{greeting_text}'")
    print("=" * 60)

    tts = TTSManager()
    if not tts.enabled:
        print("[Lỗi] TTS_ENABLED đang là False trong cấu hình.")
        return

    sentences = tts.split_into_sentences(greeting_text)
    print(f"-> Tách thành {len(sentences)} câu nhỏ để tổng hợp mượt mà:")
    for i, s in enumerate(sentences):
        print(f"   [{i}] '{s}'")

    chunks = []
    for idx, sentence in enumerate(sentences):
        clean_s = sentence.strip()
        if not clean_s:
            continue
        print(f"-> Đang sinh âm thanh cho câu [{idx}]: '{clean_s}'...")
        audio_b64 = tts.synthesize_sentence_base64(clean_s)
        if audio_b64:
            chunks.append({
                "index": idx,
                "text": clean_s,
                "audio": audio_b64
            })
            print(f"   ✓ Đã tạo xong chunk {idx} ({len(audio_b64)} chars base64)")
        else:
            print(f"   ✗ Không thể tạo audio cho chunk {idx}")

    cache_data = {
        "text": greeting_text,
        "chunks": chunks
    }

    cache_path = ROOT / "ai_engine" / "greeting_cache.json"
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2)

    print("=" * 60)
    print(f"  ✓ ĐÃ LƯU THÀNH CÔNG VÀO: {cache_path}")
    print("=" * 60)


if __name__ == "__main__":
    generate_greeting_cache()
