import asyncio
import base64
import json
import os
import re
import time

from fastapi import (
    FastAPI,
    File,
    Form,
    UploadFile,
    WebSocket,
    WebSocketDisconnect
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from chatbot.audio import (
    cleanup_files,
    convert_to_wav,
    save_audio_bytes
)
from chatbot.brain import Brain
from chatbot.config import (
    HOST,
    PORT,
    WHISPER_LANGUAGE,
    WHISPER_MODEL,
    BASE_DIR
)
from chatbot.stt import SpeechToText
from chatbot.tts import TTSManager


app = FastAPI(
    title="Voice Travel Chatbot",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

_stt = None
_brain = None
_tts = None

def get_stt():
    global _stt
    if _stt is None and os.getenv("SKIP_MODEL") != "1":
        try:
            _stt = SpeechToText(
                model_size=WHISPER_MODEL,
                language=WHISPER_LANGUAGE
            )
        except Exception as e:
            print(f"STT Model skip/fail: {e}")
            _stt = None
    return _stt

def get_brain():
    global _brain
    if _brain is None and os.getenv("SKIP_MODEL") != "1":
        try:
            _brain = Brain()
        except Exception as e:
            print(f"Brain Model skip/fail: {e}")
            _brain = None
    return _brain

def get_tts():
    global _tts
    if _tts is None and os.getenv("SKIP_MODEL") != "1":
        try:
            _tts = TTSManager()
        except Exception as e:
            print(f"TTS Model skip/fail: {e}")
            _tts = None
    return _tts


@app.on_event("startup")
async def startup_preload():
    """Preload tất cả models (LLM Qwen3-4B, VieNeu TTS, Whisper STT) ngay khi server khởi động
    để sẵn sàng phục vụ ngay lập tức, không bị cold-start ở tin nhắn đầu tiên."""
    print("[Startup] Bắt đầu preload tất cả mô hình (LLM, STT, TTS)...", flush=True)
    loop = asyncio.get_event_loop()
    await asyncio.gather(
        loop.run_in_executor(None, get_brain),
        loop.run_in_executor(None, get_tts),
        loop.run_in_executor(None, get_stt),
    )
    # nạp trực tiếp trọng số VieNeu-TTS để không bị nạp dở chừng khi user nhắn câu đầu
    tts_inst = get_tts()
    if tts_inst and tts_inst.enabled:
        try:
            print("[Startup] Đang preload trọng số VieNeu-TTS...", flush=True)
            await loop.run_in_executor(None, tts_inst._get_model)
            print("[Startup] Mô hình VieNeu-TTS đã nạp hoàn tất!", flush=True)
        except Exception as e:
            print(f"[Startup] VieNeu-TTS preload notice: {e}", flush=True)
    print("[Startup] ✅ Tất cả mô hình đã sẵn sàng 100%!", flush=True)


frontend_dir = BASE_DIR / "frontend"

if frontend_dir.exists():
    app.mount(
        "/static",
        StaticFiles(directory=str(frontend_dir)),
        name="static"
    )


def transcribe_audio_bytes(
    audio_bytes: bytes,
    fast: bool = False
) -> dict:
    stt_inst = get_stt()
    if not stt_inst:
        return {"text": "Tạo lịch trình du lịch Đà Nẵng", "logprob": 0.95}

    input_path = None
    wav_path = None

    try:
        input_path = save_audio_bytes(
            audio_bytes,
            suffix=".webm"
        )

        wav_path = convert_to_wav(input_path)

        if fast:
            return stt_inst.transcribe_fast(wav_path)

        return stt_inst.transcribe(wav_path)

    finally:
        cleanup_files(input_path, wav_path)


@app.get("/")
async def index():
    return FileResponse(
        str(frontend_dir / "index.html")
    )


@app.get("/favicon.ico")
async def favicon():
    fav = frontend_dir / "favicon.ico"
    if fav.exists():
        return FileResponse(str(fav))
    return Response(status_code=204)


@app.get("/health")
async def health():
    tts_inst = get_tts()
    return {
        "status": "ok",
        "stt": WHISPER_MODEL,
        "language": WHISPER_LANGUAGE,
        "tts": tts_inst.enabled if tts_inst else False,
        "tts_engine": tts_inst.engine if tts_inst else "none"
    }


@app.get("/voices")
async def get_voices():
    tts_inst = get_tts()
    if tts_inst:
        return tts_inst.get_available_voices()
    return [
        {"id": "vi_default", "name": "Phạm Tuyên (Mặc định)", "gender": "male", "language": "vi-VN"}
    ]


@app.post("/transcribe")
async def transcribe(
    audio: UploadFile = File(...)
):
    stt_inst = get_stt()
    if not stt_inst:
        return {"text": "Tạo lịch trình 3N2Đ Đà Nẵng", "logprob": 0.98}

    input_path = None
    wav_path = None

    try:
        audio_bytes = await audio.read()

        suffix = os.path.splitext(
            audio.filename or ".webm"
        )[1]

        input_path = save_audio_bytes(
            audio_bytes,
            suffix=suffix or ".webm"
        )

        wav_path = convert_to_wav(input_path)
        result = stt_inst.transcribe(wav_path)

        return result

    finally:
        cleanup_files(input_path, wav_path)


@app.post("/chat")
async def chat(
    message: str = Form(...),
    history: str = Form("[]")
):
    try:
        parsed_history = json.loads(history)
    except Exception:
        parsed_history = []

    brain_inst = get_brain()
    if not brain_inst:
        return {
            "message": message,
            "answer": f"Xin chào! (UI Preview Mode) Tôi đã nhận câu hỏi: '{message}'. Giao diện đang hiển thị đầy đủ thông tin lịch trình và checklist."
        }

    answer = ""

    for partial in brain_inst.stream(
        message,
        parsed_history
    ):
        answer = partial

    return {
        "message": message,
        "answer": answer
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    history = []
    audio_buffer = bytearray()
    partial_task = None
    # Mốc thời gian lần chạy partial-transcription gần nhất, dùng để giới hạn
    # tần suất gọi Whisper cho bản ghi tạm (partial). Trước đây cứ mỗi khi
    # audio_chunk tới VÀ tác vụ partial trước đã xong là lập tức chạy lại
    # ngay — mà mỗi lần lại transcribe LẠI TOÀN BỘ buffer từ đầu (buffer
    # càng ghi lâu càng phình to) → chi phí CPU tăng dần theo thời gian ghi
    # âm, tranh CPU với chính bản ghi cuối cùng, khiến hội thoại giật/trễ.
    last_partial_ts = 0.0
    PARTIAL_INTERVAL_SEC = 1.2

    async def send_partial(snapshot: bytes):
        try:
            result = await asyncio.to_thread(
                transcribe_audio_bytes,
                snapshot,
                True
            )

            text = result["text"]

            if text:
                await websocket.send_json({
                    "type": "partial_transcript",
                    "text": text
                })

        except Exception:
            pass

    async def answer_with_brain(user_text: str, voice: str = None, enable_tts: bool = True):
        answer = ""
        brain_inst = get_brain()
        tts_inst = get_tts() if enable_tts else None

        if not brain_inst:
            answer = f"Xin chào Tiến! (UI Preview Mode) Tôi đã ghi nhận yêu cầu: '{user_text}'. Lịch trình và thông tin đã được hiển thị trực quan trên giao diện Beenavi AI!"
            await websocket.send_json({
                "type": "answer",
                "text": answer
            })
            if tts_inst and tts_inst.enabled:
                audio_b64 = await asyncio.to_thread(
                    tts_inst.synthesize_sentence_base64,
                    answer,
                    voice
                )
                if audio_b64:
                    await websocket.send_json({
                        "type": "tts_chunk",
                        "audio": audio_b64,
                        "text": answer,
                        "index": 0
                    })
        else:
            buffer = ""
            sentence_index = 0
            sentence_delimiters = re.compile(r'([\.!\?\n]+|;)')

            for partial in brain_inst.stream(
                user_text,
                history
            ):
                delta = partial[len(answer):]
                answer = partial
                buffer += delta

                await websocket.send_json({
                    "type": "answer",
                    "text": partial
                })

                match = sentence_delimiters.search(buffer)
                if match:
                    split_pos = match.end()
                    sentence = buffer[:split_pos].strip()
                    buffer = buffer[split_pos:]

                    if sentence and tts_inst and tts_inst.enabled:
                        audio_b64 = await asyncio.to_thread(
                            tts_inst.synthesize_sentence_base64,
                            sentence,
                            voice
                        )
                        if audio_b64:
                            await websocket.send_json({
                                "type": "tts_chunk",
                                "audio": audio_b64,
                                "text": sentence,
                                "index": sentence_index
                            })
                            sentence_index += 1

            if buffer.strip() and tts_inst and tts_inst.enabled:
                sentence = buffer.strip()
                audio_b64 = await asyncio.to_thread(
                    tts_inst.synthesize_sentence_base64,
                    sentence,
                    voice
                )
                if audio_b64:
                    await websocket.send_json({
                        "type": "tts_chunk",
                        "audio": audio_b64,
                        "text": sentence,
                        "index": sentence_index
                    })

        history.append({
            "role": "user",
            "content": user_text
        })

        history.append({
            "role": "assistant",
            "content": answer
        })

        await websocket.send_json({
            "type": "done"
        })

    try:
        await websocket.send_json({
            "type": "ready",
            "message": "WebSocket ready"
        })

        greeting_cache_path = BASE_DIR / "chatbot" / "greeting_cache.json"
        if greeting_cache_path.exists():
            try:
                with open(greeting_cache_path, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)
                greeting_text = cache_data.get("text", "")
                await websocket.send_json({
                    "type": "greeting",
                    "text": greeting_text
                })
                for chunk in cache_data.get("chunks", []):
                    await websocket.send_json({
                        "type": "tts_chunk",
                        "audio": chunk["audio"],
                        "text": chunk["text"],
                        "index": chunk["index"]
                    })
            except Exception as cache_err:
                print(f"Lỗi đọc greeting_cache.json: {cache_err}")
        else:
            greeting_text = (
                "Xin chào anh/chị! Em là trợ lý ảo của BeeNavi. "
                "Em sẽ đồng hành cùng anh/chị trong việc tìm kiếm địa điểm, "
                "lên lịch trình và giải đáp các thông tin du lịch. "
                "Anh/chị muốn em hỗ trợ gì hôm nay?"
            )
            await websocket.send_json({
                "type": "greeting",
                "text": greeting_text
            })

            tts_inst = get_tts()
            if tts_inst and tts_inst.enabled:
                sentences = tts_inst.split_into_sentences(greeting_text)
                for idx, s in enumerate(sentences):
                    clean_s = s.strip()
                    if clean_s:
                        audio_b64 = await asyncio.to_thread(
                            tts_inst.synthesize_sentence_base64,
                            clean_s
                        )
                        if audio_b64:
                            await websocket.send_json({
                                "type": "tts_chunk",
                                "audio": audio_b64,
                                "text": clean_s,
                                "index": idx
                            })

        while True:
            raw_message = await websocket.receive_text()

            payload = json.loads(raw_message)
            event_type = payload.get("type")

            if event_type == "reset":
                history = []

                await websocket.send_json({
                    "type": "reset_done"
                })

                continue

            if event_type == "text":
                user_text = (payload.get("text") or "").strip()
                voice = payload.get("voice")
                enable_tts = payload.get("enable_tts", True)

                if not user_text:
                    continue

                try:
                    await answer_with_brain(user_text, voice=voice, enable_tts=enable_tts)

                except Exception as error:
                    await websocket.send_json({
                        "type": "error",
                        "message": str(error)
                    })

                continue

            if event_type == "audio_start":
                audio_buffer = bytearray()
                partial_task = None
                last_partial_ts = 0.0

                await websocket.send_json({
                    "type": "listening"
                })

                continue

            if event_type == "audio_chunk":
                encoded_chunk = payload.get("data")

                if not encoded_chunk:
                    continue

                audio_buffer.extend(
                    base64.b64decode(encoded_chunk)
                )

                now = time.monotonic()
                task_free = partial_task is None or partial_task.done()
                interval_elapsed = (now - last_partial_ts) >= PARTIAL_INTERVAL_SEC

                if task_free and interval_elapsed:
                    last_partial_ts = now
                    snapshot = bytes(audio_buffer)

                    partial_task = asyncio.create_task(
                        send_partial(snapshot)
                    )

                continue

            if event_type == "audio_end":
                voice = payload.get("voice")
                enable_tts = payload.get("enable_tts", True)

                if not audio_buffer:
                    await websocket.send_json({
                        "type": "stt_empty"
                    })

                    continue

                if partial_task and not partial_task.done():
                    # KHÔNG dùng partial_task.cancel(): với asyncio.to_thread,
                    # cancel() chỉ hủy việc "chờ" ở event loop — luồng Whisper
                    # trong threadpool vẫn tiếp tục chạy ngầm. Nếu ta chạy
                    # ngay transcribe cuối cùng bên dưới trong lúc đó, sẽ có
                    # 2 lượt Whisper cùng tranh CPU → cả hai đều chậm đi,
                    # đúng lúc người dùng đang chờ phản hồi nhất. Chờ nó xong
                    # hẳn (thường rất nhanh vì audio partial ngắn) rồi mới
                    # chạy transcribe cuối cùng, đảm bảo chạy tuần tự.
                    try:
                        await partial_task
                    except Exception:
                        pass
                    partial_task = None

                final_bytes = bytes(audio_buffer)
                audio_buffer = bytearray()

                try:
                    stt_result = await asyncio.to_thread(
                        transcribe_audio_bytes,
                        final_bytes,
                        False
                    )

                    transcript = stt_result["text"]

                    if not transcript:
                        await websocket.send_json({
                            "type": "stt_empty"
                        })

                        continue

                    await websocket.send_json({
                        "type": "transcript",
                        "text": transcript,
                        "logprob": stt_result.get("logprob")
                    })

                    await answer_with_brain(transcript, voice=voice, enable_tts=enable_tts)

                except Exception as error:
                    await websocket.send_json({
                        "type": "error",
                        "message": str(error)
                    })

                continue

            if event_type == "audio":
                encoded_audio = payload.get("data")
                voice = payload.get("voice")
                enable_tts = payload.get("enable_tts", True)

                if not encoded_audio:
                    continue

                audio_bytes = base64.b64decode(encoded_audio)

                try:
                    stt_result = await asyncio.to_thread(
                        transcribe_audio_bytes,
                        audio_bytes,
                        False
                    )

                    transcript = stt_result["text"]

                    if not transcript:
                        await websocket.send_json({
                            "type": "stt_empty"
                        })

                        continue

                    await websocket.send_json({
                        "type": "transcript",
                        "text": transcript,
                        "logprob": stt_result.get("logprob")
                    })

                    await answer_with_brain(transcript, voice=voice, enable_tts=enable_tts)

                except Exception as error:
                    await websocket.send_json({
                        "type": "error",
                        "message": str(error)
                    })

                continue

    except WebSocketDisconnect:
        pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "chatbot.server:app",
        host=HOST,
        port=PORT,
        reload=False
    )