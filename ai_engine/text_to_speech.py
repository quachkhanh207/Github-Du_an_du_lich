"""
Module quản lý và tổng hợp giọng nói (Text-to-Speech) cho Beenavi Chatbot.

Hỗ trợ 2 chế độ (Dual-Engine):
1. 'vieneu': Chạy trực tiếp mô hình VieNeu-TTS in-process (GPU CUDA / CPU ONNX).
2. 'remote_api': Gửi HTTP POST request tới dịch vụ TTS_Source độc lập.
"""

import base64
import io
import contextlib
import logging
import os
import re
import threading
from typing import List, Tuple, Dict, Any, Optional

import numpy as np
from scipy.io import wavfile

from api_server.config import (
    BASE_DIR,
    TEMP_DIR,
    TTS_API_URL,
    TTS_DEVICE,
    TTS_ENABLED,
    TTS_ENGINE,
    TTS_VOICE,
)

logger = logging.getLogger(__name__)


class TTSManager:
    """
    Quản lý tổng hợp giọng nói VieNeu-TTS với hỗ trợ streaming theo từng câu.
    """

    _model_lock = threading.Lock()
    _infer_lock = threading.Lock()

    def __init__(self) -> None:
        self.enabled = TTS_ENABLED
        self.engine = TTS_ENGINE
        self.default_voice = TTS_VOICE
        self.api_url = TTS_API_URL.rstrip("/")
        self.device_setting = TTS_DEVICE

        self._model = None
        self._sample_rate = 24000

        logger.info(
            "TTSManager đã khởi tạo | Enabled=%s | Engine=%s | Default Voice=%s",
            self.enabled,
            self.engine,
            self.default_voice
        )

    def _resolve_device(self) -> str:
        """Phân giải cấu hình GPU/CPU cho mô hình VieNeu-TTS."""
        dev = self.device_setting.lower().strip()
        try:
            import torch
            cuda_available = torch.cuda.is_available()
            if dev == "auto":
                return "cuda" if cuda_available else "cpu"
            if dev == "cuda":
                if not cuda_available:
                    logger.warning("TTS_DEVICE=cuda nhưng GPU CUDA không khả dụng. Switch sang CPU.")
                    return "cpu"
                return "cuda"
            return "cpu"
        except ImportError:
            return "cpu"

    def _get_model(self):
        """Lazy-loading mô hình VieNeu-TTS (Thread-safe Singleton)."""
        if self._model is None:
            with self._model_lock:
                if self._model is None:
                    try:
                        from vieneu import Vieneu
                        device = self._resolve_device()
                        logger.info("Đang nạp mô hình VieNeu-TTS trên thiết bị: %s...", device)
                        self._model = Vieneu(device=device)
                        if hasattr(self._model, "sample_rate") and self._model.sample_rate:
                            self._sample_rate = self._model.sample_rate
                        logger.info("Mô hình VieNeu-TTS đã nạp thành công!")
                    except ImportError:
                        logger.error(
                            "Chưa cài đặt thư viện 'vieneu'. Hãy chạy: pip install vieneu"
                        )
                        raise RuntimeError("Thư viện vieneu chưa được cài đặt.")
                    except Exception as e:
                        logger.exception("Lỗi khởi tạo mô hình VieNeu-TTS: %s", e)
                        raise RuntimeError(f"Không thể nạp mô hình VieNeu-TTS: {e}")
        return self._model

    @staticmethod
    def split_into_sentences(text: str) -> List[str]:
        """
        Tách văn bản thành các câu/cụm câu tự nhiên dựa trên dấu câu tiếng Việt.
        """
        if not text or not text.strip():
            return []

        # Tách theo các dấu kết thúc câu hoặc dấu phẩy/xuống dòng
        pattern = r'([\.!\?\n]+|;)'
        parts = re.split(pattern, text)

        sentences = []
        current = ""

        for part in parts:
            if not part:
                continue
            current += part
            if re.search(pattern, part):
                cleaned = current.strip()
                if cleaned:
                    sentences.append(cleaned)
                current = ""

        if current.strip():
            sentences.append(current.strip())

        return sentences

    def get_available_voices(self) -> List[Dict[str, str]]:
        """Trả về danh sách giọng đọc hỗ trợ (chỉ sử dụng 1 giọng Phạm Tuyên)."""
        return [
            {
                "id": "vi_default",
                "name": "Phạm Tuyên (Mặc định)",
                "gender": "male",
                "language": "vi-VN",
                "description": "Giọng nam Bắc tự nhiên — Phạm Tuyên",
            }
        ]

    def synthesize_sentence(
        self,
        text: str,
        voice: Optional[str] = None
    ) -> Optional[bytes]:
        """
        Tổng hợp giọng nói cho 1 câu văn bản ngắn và trả về bytes WAV (luôn dùng giọng Phạm Tuyên).
        """
        if not self.enabled or not text or not text.strip():
            return None

        clean_text = text.strip()
        selected_voice = None  # Force giọng Phạm Tuyên (vi_default)

        if self.engine == "remote_api":
            return self._synthesize_remote(clean_text, selected_voice)

        return self._synthesize_local(clean_text, selected_voice)

    def _synthesize_local(self, text: str, voice: Optional[str]) -> Optional[bytes]:
        """Tổng hợp bằng VieNeu-TTS in-process."""
        try:
            tts = self._get_model()
            sample_rate = getattr(tts, "sample_rate", 24000) or 24000

            with self._infer_lock:
                try:
                    import torch
                    if torch.cuda.is_available():
                        with torch.inference_mode(), torch.amp.autocast("cuda", dtype=torch.float16):
                            if voice:
                                audio_raw = tts.infer(text=text, voice=voice)
                            else:
                                audio_raw = tts.infer(text=text)
                    else:
                        if voice:
                            audio_raw = tts.infer(text=text, voice=voice)
                        else:
                            audio_raw = tts.infer(text=text)
                except Exception:
                    if voice:
                        audio_raw = tts.infer(text=text, voice=voice)
                    else:
                        audio_raw = tts.infer(text=text)

            # Chuyển đổi audio_raw về numpy array
            if hasattr(audio_raw, "detach"):
                data_float = audio_raw.detach().cpu().numpy().squeeze().astype(np.float32)
            elif isinstance(audio_raw, np.ndarray):
                data_float = audio_raw.squeeze().astype(np.float32)
            else:
                return None

            if len(data_float) == 0:
                return None

            # Cross-fading 5ms để tránh tiếng click ở đầu/cuối
            fade_samples = int(0.005 * sample_rate)
            if fade_samples > 0 and len(data_float) > 2 * fade_samples:
                fade_in = np.linspace(0.0, 1.0, fade_samples, dtype=np.float32)
                fade_out = np.linspace(1.0, 0.0, fade_samples, dtype=np.float32)
                data_float[:fade_samples] *= fade_in
                data_float[-fade_samples:] *= fade_out

            # Chuẩn hóa biên độ
            max_val = np.max(np.abs(data_float))
            if max_val > 0:
                data_float = data_float / max_val

            final_int16 = np.int16(data_float * 32767)

            buf = io.BytesIO()
            wavfile.write(buf, sample_rate, final_int16)
            return buf.getvalue()

        except Exception as e:
            logger.exception("Lỗi tổng hợp VieNeu local cho câu '%s': %s", text[:30], e)
            return None

    def _synthesize_remote(self, text: str, voice: Optional[str]) -> Optional[bytes]:
        """Gọi tới TTS_Source HTTP REST API làm fallback/remote service."""
        try:
            import httpx
            payload = {
                "segments": [{"text": text, "start": 0.0}],
                "voice": voice or "vi_default"
            }
            url = f"{self.api_url}/api/v1/generate-tts"
            resp = httpx.post(url, json=payload, timeout=10.0)
            if resp.status_code == 200:
                return resp.content
            logger.error("Remote TTS API error %d: %s", resp.status_code, resp.text)
            return None
        except Exception as e:
            logger.exception("Lỗi kết nối tới Remote TTS API (%s): %s", self.api_url, e)
            return None

    def synthesize_sentence_base64(
        self,
        text: str,
        voice: Optional[str] = None
    ) -> Optional[str]:
        """Tổng hợp giọng nói và trả về chuỗi Base64 (dễ dàng gửi qua WebSocket JSON)."""
        raw_bytes = self.synthesize_sentence(text, voice)
        if raw_bytes:
            return base64.b64encode(raw_bytes).decode("utf-8")
        return None

    def synthesize_stream_base64(
        self,
        text: str,
        voice: Optional[str] = None
    ):
        """Tổng hợp giọng nói streaming, trả về generator các chunk Base64 (WAV)."""
        if not self.enabled or not text or not text.strip():
            return

        clean_text = text.strip()
        selected_voice = None  # Force vi_default

        if self.engine == "remote_api":
            b64 = self.synthesize_sentence_base64(clean_text, selected_voice)
            if b64:
                yield b64
            return

        try:
            tts = self._get_model()
            sample_rate = getattr(tts, "sample_rate", 24000) or 24000
            
            buffer_samples = []
            min_chunk_size = int(0.625 * sample_rate)

            with self._infer_lock:
                import torch
                ctx = torch.inference_mode() if torch.cuda.is_available() else contextlib.nullcontext()
                with ctx:
                    if hasattr(tts, "infer_stream"):
                        amp_ctx = torch.amp.autocast("cuda", dtype=torch.float16) if torch.cuda.is_available() else contextlib.nullcontext()
                        with amp_ctx:
                            iterator = tts.infer_stream(text=clean_text, voice=selected_voice) if selected_voice else tts.infer_stream(text=clean_text)
                            for audio_raw in iterator:
                                if hasattr(audio_raw, "detach"):
                                    data_float = audio_raw.detach().cpu().numpy().squeeze().astype(np.float32)
                                elif isinstance(audio_raw, np.ndarray):
                                    data_float = audio_raw.squeeze().astype(np.float32)
                                else:
                                    continue
                                    
                                if len(data_float) > 0:
                                    buffer_samples.append(data_float)
                                    
                                current_len = sum(len(x) for x in buffer_samples)
                                if current_len >= min_chunk_size:
                                    combined = np.concatenate(buffer_samples)
                                    buffer_samples = []
                                    yield self._raw_to_b64_wav(combined, sample_rate)
                                    
                            if buffer_samples:
                                combined = np.concatenate(buffer_samples)
                                yield self._raw_to_b64_wav(combined, sample_rate)
                    else:
                        b64 = self.synthesize_sentence_base64(clean_text, selected_voice)
                        if b64:
                            yield b64

        except Exception as e:
            logger.exception("Lỗi stream VieNeu local: %s", e)

    def _raw_to_b64_wav(self, data_float: np.ndarray, sample_rate: int) -> str:
        data_float = np.clip(data_float, -1.0, 1.0)
        final_int16 = np.int16(data_float * 32767)
        buf = io.BytesIO()
        wavfile.write(buf, sample_rate, final_int16)
        return base64.b64encode(buf.getvalue()).decode("utf-8")
