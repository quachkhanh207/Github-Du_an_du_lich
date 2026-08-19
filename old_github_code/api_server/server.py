import asyncio
import base64
import json
import os
import re
import time
from typing import Optional, List, Dict, Any

import httpx

from fastapi import (
    FastAPI,
    File,
    Form,
    Request,
    UploadFile,
    WebSocket,
    WebSocketDisconnect
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from ai_engine.audio_processor import (
    cleanup_files,
    convert_to_wav,
    save_audio_bytes
)
from ai_engine.brain import Brain
from api_server.config import (
    HOST,
    PORT,
    WHISPER_LANGUAGE,
    WHISPER_MODEL,
    BASE_DIR
)
from ai_engine.speech_to_text import SpeechToText
from ai_engine.text_to_speech import TTSManager
from ai_engine.orchestrator import AIOrchestrator
from planner.rag_engine import RagEngine


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
_rag = None
_orchestrator = None

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

def get_rag():
    global _rag
    if _rag is None:
        try:
            index_path = BASE_DIR / "data" / "locations_index.json"
            _rag = RagEngine(str(index_path))
            _rag.load_index()
        except Exception as e:
            print(f"RAG Engine skip/fail: {e}")
            _rag = None
    return _rag

def get_orchestrator():
    global _orchestrator
    if _orchestrator is None:
        brain_inst = get_brain()
        rag_inst = get_rag()
        _orchestrator = AIOrchestrator(brain=brain_inst, rag_engine=rag_inst)
    return _orchestrator

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
        loop.run_in_executor(None, get_rag),
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
        return {"text": "", "error": "STT_UNAVAILABLE", "logprob": 0.0}

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


@app.get("/location")
def get_location(name: str):
    rag_inst = get_rag()
    if rag_inst:
        loc = rag_inst.find_exact_location(name)
        if loc:
            return loc
    return {"error": "Not found"}


@app.get("/api/weather")
def api_weather(destination: str = "Đà Nẵng", lat: float = 0.0, lon: float = 0.0):
    """Lấy thời tiết thực tế từ OpenWeatherMap kèm Quy Tắc Lựa Chọn Hoạt Động (Weather Rules)."""
    from geo_services.weather_service import get_weather_by_destination, get_realtime_weather

    if lat != 0.0 and lon != 0.0:
        weather_info = get_realtime_weather(lat, lon)
        weather_info["destination"] = destination
        weather_info["lat"] = lat
        weather_info["lon"] = lon
        return weather_info

    return get_weather_by_destination(destination)


@app.post("/api/generate_itinerary")

async def api_generate_itinerary(request: Request):
    """Tạo lịch trình động theo RAG Engine (17.147 POIs) và thời tiết thực tế."""
    try:
        body = await request.json()
    except Exception:
        body = {}

    dest = body.get("destination", "Đà Nẵng")
    rag_inst = get_rag()

    if rag_inst:
        structured = rag_inst.get_structured_itinerary(body)
    else:
        structured = {
            "destination": dest,
            "title": f"Lịch Trình • {dest}",
            "days": []
        }

    # Lấy thông tin thời tiết
    weather = api_weather(destination=dest)
    weather_tag = weather.get("weather_tag", "Nắng")
    weather_icon = "☀️"
    if "mưa" in weather_tag.lower():
        weather_icon = "🌧️"
    elif "lạnh" in weather_tag.lower():
        weather_icon = "❄️"
    elif "gió" in weather_tag.lower() or "ẩm" in weather_tag.lower():
        weather_icon = "🌫️"

    structured["weather"] = {
        "icon": weather_icon,
        "temp": f"{weather.get('temp', 28)}°C",
        "desc": f"{dest} • {weather.get('description', 'Thời tiết lý tưởng du lịch')}",
        "weather_tag": weather_tag
    }

    # Tọa độ trung tâm điểm đến cho Leaflet Map
    structured["center"] = [weather.get("lat", 16.068), weather.get("lon", 108.230)]

    return structured



@app.post("/transcribe")
async def transcribe(
    audio: UploadFile = File(...)
):
    stt_inst = get_stt()
    if not stt_inst:
        return {"text": "", "error": "STT_UNAVAILABLE", "logprob": 0.0}

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
    history: str = Form("[]"),
    trip_data: str = Form("{}"),
    session_id: Optional[str] = Form(None),
    user_id: Optional[str] = Form(None)
):
    """Endpoint trò chuyện du lịch điều phối bởi AI Orchestrator."""
    try:
        parsed_trip_data = json.loads(trip_data)
    except Exception:
        parsed_trip_data = {}

    orchestrator = get_orchestrator()
    final_res = {}

    async for chunk in orchestrator.stream_chat(
        user_text=message,
        session_id=session_id,
        user_id=user_id,
        explicit_trip_data=parsed_trip_data
    ):
        if chunk.get("type") in ("answer", "clarification"):
            final_res = chunk

    answer = final_res.get("text", "")
    weather_info_result = final_res.get("weather")
    structured_itinerary = final_res.get("structured_itinerary")
    map_markers = final_res.get("map_markers", [])
    budget_breakdown = final_res.get("budget_breakdown")
    smart_checklist = final_res.get("smart_checklist")

    return {
        "message": message,
        "answer": answer,
        "weather": weather_info_result,
        "structured_itinerary": structured_itinerary,
        "map_markers": map_markers,
        "budget_breakdown": budget_breakdown,
        "smart_checklist": smart_checklist,
        "intent": final_res.get("intent"),
        "slots": final_res.get("slots"),
        "session_id": final_res.get("session_id"),
        "tools_called": final_res.get("tools_called", [])
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    audio_buffer = bytearray()
    partial_task = None
    last_partial_ts = 0.0
    PARTIAL_INTERVAL_SEC = 1.2
    ws_session_id = str(uuid.uuid4())

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

    async def answer_with_orchestrator(user_text: str, voice: str = None, enable_tts: bool = True, user_id: str = None):
        orchestrator = get_orchestrator()
        tts_inst = get_tts() if enable_tts else None

        buffer = ""
        sentence_index = 0
        sentence_delimiters = re.compile(r'([\.!\?\n]+|;)')
        last_full_text = ""

        async for chunk in orchestrator.stream_chat(
            user_text=user_text,
            session_id=ws_session_id,
            user_id=user_id
        ):
            chunk_type = chunk.get("type")
            text = chunk.get("text", "")

            if chunk_type in ("partial_answer", "answer"):
                delta = text[len(last_full_text):]
                last_full_text = text
                buffer += delta

                res_payload = {
                    "type": "answer",
                    "text": text,
                    "intent": chunk.get("intent"),
                    "weather": chunk.get("weather"),
                    "structured_itinerary": chunk.get("structured_itinerary"),
                    "map_markers": chunk.get("map_markers", []),
                    "budget_breakdown": chunk.get("budget_breakdown"),
                    "smart_checklist": chunk.get("smart_checklist"),
                    "session_id": ws_session_id
                }
                await websocket.send_json(res_payload)

                # Bắn event map_sync riêng nếu có markers mới
                if chunk.get("map_markers"):
                    await websocket.send_json({
                        "type": "map_sync",
                        "markers": chunk.get("map_markers"),
                        "destination": chunk.get("slots", {}).get("destination", "")
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

        await websocket.send_json({
            "type": "done",
            "session_id": ws_session_id
        })

    try:
        await websocket.send_json({
            "type": "ready",
            "message": "WebSocket ready"
        })

        greeting_cache_path = BASE_DIR / "ai_engine" / "greeting_cache.json"
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
                orchestrator = get_orchestrator()
                orchestrator.state_manager.clear_session_slots(ws_session_id)

                await websocket.send_json({
                    "type": "reset_done",
                    "session_id": ws_session_id
                })

                continue

            if event_type == "text":
                user_text = (payload.get("text") or "").strip()
                voice = payload.get("voice")
                enable_tts = payload.get("enable_tts", True)
                user_id = payload.get("user_id")

                if not user_text:
                    continue

                try:
                    await answer_with_orchestrator(user_text, voice=voice, enable_tts=enable_tts, user_id=user_id)

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
                user_id = payload.get("user_id")

                if not audio_buffer:
                    await websocket.send_json({
                        "type": "stt_empty"
                    })

                    continue

                if partial_task and not partial_task.done():
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

                    await answer_with_orchestrator(transcript, voice=voice, enable_tts=enable_tts, user_id=user_id)

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
                user_id = payload.get("user_id")

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

                    await answer_with_orchestrator(transcript, voice=voice, enable_tts=enable_tts, user_id=user_id)

                except Exception as error:
                    await websocket.send_json({
                        "type": "error",
                        "message": str(error)
                    })

                continue

    except WebSocketDisconnect:
        pass


# ──────────────────────────────────────────────────────────────────────────────
# QUẢN LÝ NGƯỜI DÙNG, NHẬT KÝ & LỊCH SỬ DU LỊCH
# ──────────────────────────────────────────────────────────────────────────────
import diary_service


def get_current_user_id(request: Request) -> Optional[str]:
    """Trích xuất User ID từ Authorization Header (Bearer token)"""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:].strip()
        if token.startswith("token_"):
            return token[6:]
        return token
    return None


# 1. User & Auth Endpoints
@app.post("/api/users/register")
@app.post("/api/v1/users/register/")
async def api_register(request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    username = body.get("username", "").strip()
    email = body.get("email", "").strip()
    password = body.get("password", "").strip()
    full_name = body.get("full_name", "").strip()

    if not username or not password:
        return Response(
            content=json.dumps({"detail": "Vui lòng nhập tên đăng nhập và mật khẩu"}),
            status_code=400,
            media_type="application/json"
        )
    try:
        user = diary_service.register_user(username, email or f"{username}@beenavi.vn", password, full_name)
        profile = diary_service.get_user_profile(user["id"])
        return {
            "token": f"token_{user['id']}",
            "user": user,
            "profile": profile
        }
    except ValueError as e:
        return Response(content=json.dumps({"detail": str(e)}), status_code=400, media_type="application/json")


@app.post("/api/users/login")
@app.post("/api/v1/users/login/")
async def api_login(request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    username = body.get("username", "").strip()
    password = body.get("password", "").strip()

    user = diary_service.authenticate_user(username, password)
    if not user:
        return Response(
            content=json.dumps({"detail": "Tên đăng nhập hoặc mật khẩu không chính xác"}),
            status_code=401,
            media_type="application/json"
        )
    profile = diary_service.get_user_profile(user["id"])
    return {"token": f"token_{user['id']}", "user": user, "profile": profile}


@app.get("/api/users/profile")
@app.get("/api/v1/users/profile/")
async def api_get_profile(request: Request, user_id: str = None):
    uid = user_id or get_current_user_id(request)
    if not uid:
        return Response(
            content=json.dumps({"detail": "Vui lòng đăng nhập"}),
            status_code=401,
            media_type="application/json"
        )
    profile = diary_service.get_user_profile(uid)
    if not profile:
        return Response(
            content=json.dumps({"detail": "Không tìm thấy người dùng"}),
            status_code=404,
            media_type="application/json"
        )
    return profile


@app.put("/api/users/profile")
@app.put("/api/v1/users/profile/")
async def api_update_profile(request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    uid = body.get("user_id") or get_current_user_id(request)
    if not uid:
        return Response(
            content=json.dumps({"detail": "Vui lòng đăng nhập"}),
            status_code=401,
            media_type="application/json"
        )
    updated = diary_service.update_user_profile(uid, body)
    return updated


# 2. Trips & Itineraries Endpoints
@app.get("/api/trips")
@app.get("/api/v1/trips/")
async def api_get_trips(request: Request, user_id: str = None):
    uid = user_id or get_current_user_id(request)
    if not uid:
        return Response(
            content=json.dumps({"detail": "Vui lòng đăng nhập để xem danh sách chuyến đi"}),
            status_code=401,
            media_type="application/json"
        )
    trips = diary_service.get_user_trips(uid)
    return trips


@app.post("/api/trips")
@app.post("/api/v1/trips/")
@app.post("/api/trips/sync")
async def api_create_or_sync_trip(request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    uid = body.get("user_id") or get_current_user_id(request)
    trip = diary_service.save_or_update_trip(body, user_id=uid)
    return trip


@app.get("/api/trips/statistics")
@app.get("/api/v1/trips/statistics/")
async def api_get_statistics(request: Request, user_id: str = None):
    uid = user_id or get_current_user_id(request)
    stats = diary_service.get_user_statistics(uid)
    return stats


@app.get("/api/trips/{trip_id}")

@app.get("/api/v1/trips/{trip_id}/")
async def api_get_trip_detail(trip_id: str):
    trip = diary_service.get_trip_detail(trip_id)
    if not trip:
        return Response(content=json.dumps({"detail": "Chuyến đi không tồn tại"}), status_code=404, media_type="application/json")
    return trip


@app.delete("/api/trips/{trip_id}")
@app.delete("/api/v1/trips/{trip_id}/")
async def api_delete_trip(trip_id: str):
    diary_service.delete_trip(trip_id)
    return {"status": "success", "detail": "Đã xóa chuyến đi"}


# 3. Photos & Checklist Endpoints
@app.post("/api/trips/{trip_id}/photos")
@app.post("/api/v1/trips/{trip_id}/photos/")
async def api_add_photo(trip_id: str, request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    image_url = body.get("image_url", "https://images.unsplash.com/photo-1507525428034-b723cf961d3e")
    caption = body.get("caption", "")
    location_tag = body.get("location_tag", "")
    photo = diary_service.add_photo_to_trip(trip_id, image_url, caption, location_tag)
    return photo


@app.get("/api/trips/{trip_id}/checklist")
@app.get("/api/v1/trips/{trip_id}/checklist/")
async def api_get_trip_checklist(trip_id: str):
    items = diary_service.get_trip_checklist(trip_id)
    return items


@app.post("/api/trips/{trip_id}/checklist")
@app.post("/api/v1/trips/{trip_id}/checklist/")
async def api_add_checklist_item(trip_id: str, request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    item_name = body.get("item_name") or body.get("text") or "Đồ dùng cá nhân"
    category = body.get("category", "Đồ dùng chung")
    priority = body.get("priority", "Bắt buộc")
    quantity = int(body.get("quantity", 1))
    is_completed = int(body.get("is_completed", 0))
    item = diary_service.add_checklist_item(trip_id, item_name, category, quantity, priority, is_completed)
    return item


@app.post("/api/trips/{trip_id}/checklist/bulk")
@app.post("/api/v1/trips/{trip_id}/checklist/bulk/")
async def api_save_trip_checklist_bulk(trip_id: str, request: Request):
    try:
        body = await request.json()
    except Exception:
        body = []
    items = body if isinstance(body, list) else body.get("items", [])
    saved = diary_service.save_trip_checklist_bulk(trip_id, items)
    return saved


@app.put("/api/checklist/{item_id}")
async def api_update_checklist(item_id: str, request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    is_completed = body.get("is_completed", True)
    diary_service.update_checklist_item(item_id, is_completed)
    return {"status": "success", "item_id": item_id, "is_completed": is_completed}


@app.delete("/api/checklist/{item_id}")
async def api_delete_checklist(item_id: str):
    diary_service.delete_checklist_item(item_id)
    return {"status": "success", "item_id": item_id}


# 4. Chat History Endpoints
@app.get("/api/chat/history")
async def api_get_chat_history(session_id: str = "default", limit: int = 50):
    messages = diary_service.get_chat_history(session_id, limit)
    return messages


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api_server.server:app",
        host=HOST,
        port=PORT,
        reload=False
    )
