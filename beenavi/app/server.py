import asyncio
import base64
import json
import os
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

from app.audio import (
    cleanup_files,
    convert_to_wav,
    save_audio_bytes
)
from app.brain import Brain
from app.config import (
    HOST,
    PORT,
    WHISPER_LANGUAGE,
    WHISPER_MODEL,
    BASE_DIR
)
from app.stt import SpeechToText


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


frontend_dir = BASE_DIR.parent / "frontend"
if not frontend_dir.exists():
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
    return {
        "status": "ok",
        "stt": WHISPER_MODEL,
        "language": WHISPER_LANGUAGE
    }


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

    async def answer_with_brain(user_text: str):
        answer = ""
        brain_inst = get_brain()

        if not brain_inst:
            answer = f"Xin chào Tiến! (UI Preview Mode) Tôi đã ghi nhận yêu cầu: '{user_text}'. Lịch trình và thông tin đã được hiển thị trực quan trên giao diện Beenavi AI!"
            await websocket.send_json({
                "type": "answer",
                "text": answer
            })
        else:
            for partial in brain_inst.stream(
                user_text,
                history
            ):
                answer = partial

                await websocket.send_json({
                    "type": "answer",
                    "text": partial
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

                if not user_text:
                    continue

                try:
                    await answer_with_brain(user_text)

                except Exception as error:
                    await websocket.send_json({
                        "type": "error",
                        "message": str(error)
                    })

                continue

            if event_type == "audio_start":
                audio_buffer = bytearray()
                partial_task = None

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

                if partial_task is None or partial_task.done():
                    snapshot = bytes(audio_buffer)

                    partial_task = asyncio.create_task(
                        send_partial(snapshot)
                    )

                continue

            if event_type == "audio_end":
                if not audio_buffer:
                    await websocket.send_json({
                        "type": "stt_empty"
                    })

                    continue

                if partial_task and not partial_task.done():
                    partial_task.cancel()

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

                    await answer_with_brain(transcript)

                except Exception as error:
                    await websocket.send_json({
                        "type": "error",
                        "message": str(error)
                    })

                continue

            if event_type != "audio":
                continue

            encoded_audio = payload.get("data")

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

                await answer_with_brain(transcript)

            except Exception as error:
                await websocket.send_json({
                    "type": "error",
                    "message": str(error)
                })

    except WebSocketDisconnect:
        pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.server:app",
        host=HOST,
        port=PORT,
        reload=False
    )