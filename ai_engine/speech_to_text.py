import re
import torch
from faster_whisper import WhisperModel
from api_server.config import STT_DEVICE

# Prompt ngữ cảnh giúp Whisper nhận dạng đúng từ vựng du lịch và triệt tiêu ảo giác YouTube / Subtitles
WHISPER_TRAVEL_PROMPT = (
    "Xin chào, tôi là trợ lý ảo du lịch Beenavi. "
    "Tư vấn lên lịch trình, lộ trình du lịch Hà Nội, Đà Nẵng, TP Hồ Chí Minh, Hội An, Phú Quốc, Sa Pa, Nha Trang, "
    "thời tiết, ngân sách, khách sạn, ẩm thực, phương tiện và danh sách chuẩn bị."
)

# Danh sách mẫu ảo giác (hallucination) thường gặp của Faster-Whisper trên dữ liệu YouTube tiếng Việt
HALLUCINATION_PATTERNS = [
    r"(nếu bạn|hãy)\s*(thích|thấy hay)?\s*(mì|kênh|video)?\s*(hãy\s*)?(flow|follow|like|share|sub|subscribe|đăng ký)\s*kênh.*",
    r".*ghiền mì gõ.*",
    r".*lalago.*",
    r".*youtube.*",
    r".*gợi ý (các|những) kênh.*",
    r".*(follow|flow)\s*kênh.*",
    r".*(like|share|subscribe|đăng ký)\s*(kênh|ủng hộ|video).*",
    r".*cảm ơn (các bạn|quý vị|mọi người) đã (xem|theo dõi|lắng nghe).*",
    r".*chúc (các bạn|quý vị|mọi người) (xem phim|một ngày|vui vẻ).*",
    r".*nhớ (bấm|nhấn) (chuông|like|theo dõi).*",
    r".*hẹn gặp lại (các bạn|quý vị|mọi người) trong (những|các)? video.*",
    r".*(phụ đề|thuyết minh|vietsub|subtitles?)\s*(bởi|by|thực hiện).*",
    r".*kênh youtube.*",
    r".*kênh tiktok.*",
    r".*chúc các bạn xem.*",
    r"^(like|subscribe|share|sub|bye|cảm ơn|thank you)[\.\!\?,\s]*$"
]

COMPILED_HALLUCINATIONS = [re.compile(p, re.IGNORECASE) for p in HALLUCINATION_PATTERNS]


class SpeechToText:
    def __init__(
        self,
        model_size: str = "small",
        language: str = "vi",
        device: str | None = None
    ):
        self.language = language
        target_device = device or STT_DEVICE

        if target_device == "cuda" and torch.cuda.is_available():
            device_choice = "cuda"
            compute_type = "float16"
        else:
            device_choice = "cpu"
            compute_type = "int8"

        print(f"[STT] Loading Whisper: {model_size} on {device_choice} ({compute_type})", flush=True)

        self.model = WhisperModel(
            model_size,
            device=device_choice,
            compute_type=compute_type
        )

    @staticmethod
    def is_hallucination(text: str) -> bool:
        """Kiểm tra xem câu nhận diện có phải là ảo giác YouTube/Subtitle hay không."""
        if not text or len(text.strip()) < 2:
            return True
        clean = text.strip().lower()
        for pattern in COMPILED_HALLUCINATIONS:
            if pattern.search(clean):
                return True
        return False

    @classmethod
    def clean_and_filter(cls, text: str) -> str:
        """Lọc bỏ các đoạn ảo giác khỏi văn bản nhận dạng."""
        if not text:
            return ""
        
        # Nếu toàn bộ câu trùng mẫu ảo giác -> loại bỏ
        if cls.is_hallucination(text):
            return ""

        # Lọc từng phần nếu bị dính đuôi ảo giác
        for pattern in COMPILED_HALLUCINATIONS:
            text = pattern.sub("", text)

        return text.strip()

    @classmethod
    def normalize(cls, text: str) -> str:
        if not text:
            return ""

        text = cls.clean_and_filter(text)
        if not text:
            return ""

        text = re.sub(r"\s+", " ", text.strip())

        replacements = {
            " đà nẵng ": " Đà Nẵng ",
            " hội an ": " Hội An ",
            " hà nội ": " Hà Nội ",
            " hồ chí minh ": " Hồ Chí Minh ",
            " tphcm ": " Thành phố Hồ Chí Minh ",
            " tp hcm ": " Thành phố Hồ Chí Minh ",
            " sapa ": " Sa Pa ",
            " phú quốc ": " Phú Quốc ",
            " nha trang ": " Nha Trang ",
            " đà lạt ": " Đà Lạt "
        }

        padded = f" {text.lower()} "

        for old, new in replacements.items():
            padded = padded.replace(old, new)

        text = padded.strip()

        if text:
            text = text[0].upper() + text[1:]

        return text

    def transcribe_fast(self, audio_path: str) -> dict:
        """Nhận diện nhanh (cho realtime partial transcripts)."""
        try:
            segments, info = self.model.transcribe(
                audio_path,
                language=self.language,
                task="transcribe",
                initial_prompt=WHISPER_TRAVEL_PROMPT,
                beam_size=3,
                best_of=3,
                temperature=0.0,
                condition_on_previous_text=False,
                vad_filter=True,
                vad_parameters={
                    "min_silence_duration_ms": 350,
                    "speech_pad_ms": 150,
                    "min_speech_duration_ms": 150
                },
                word_timestamps=False
            )

            texts = []
            for segment in segments:
                seg_text = segment.text.strip()
                if seg_text and not self.is_hallucination(seg_text):
                    texts.append(seg_text)

            transcript = self.normalize(" ".join(texts))

            return {
                "text": transcript,
                "language": info.language,
                "logprob": None
            }
        except Exception as e:
            print(f"[STT] Lỗi transcribe_fast: {e}", flush=True)
            return {"text": "", "language": "vi", "logprob": None}

    def transcribe(self, audio_path: str) -> dict:
        """Nhận diện chất lượng cao khi kết thúc câu nói với Fallback đảm bảo không mất tiếng."""
        try:
            segments, info = self.model.transcribe(
                audio_path,
                language=self.language,
                task="transcribe",
                initial_prompt=WHISPER_TRAVEL_PROMPT,
                beam_size=1,
                best_of=1,
                temperature=0.0,
                condition_on_previous_text=False,
                vad_filter=True,
                vad_parameters={
                    "min_silence_duration_ms": 400,
                    "speech_pad_ms": 200,
                    "min_speech_duration_ms": 150
                },
                no_speech_threshold=0.8,
                log_prob_threshold=-1.3,
                compression_ratio_threshold=2.4,
                word_timestamps=False
            )

            texts = []
            logprobs = []

            for segment in segments:
                seg_text = segment.text.strip()
                if not seg_text:
                    continue

                if segment.avg_logprob is not None:
                    if segment.avg_logprob < -1.4:
                        continue
                    logprobs.append(segment.avg_logprob)

                if not self.is_hallucination(seg_text):
                    texts.append(seg_text)

            raw_joined = " ".join(texts)
            transcript = self.normalize(raw_joined)

            # FALLBACK: Nếu VAD lọc sạch hoặc câu quá ngắn/yếu -> transcribe trực tiếp không qua VAD filter
            if not transcript:
                fb_segments, fb_info = self.model.transcribe(
                    audio_path,
                    language=self.language,
                    task="transcribe",
                    initial_prompt=WHISPER_TRAVEL_PROMPT,
                    beam_size=1,
                    temperature=0.0,
                    vad_filter=False,
                    word_timestamps=False
                )
                fb_texts = [s.text.strip() for s in fb_segments if s.text.strip() and not self.is_hallucination(s.text.strip())]
                transcript = self.normalize(" ".join(fb_texts))

            average_logprob = None
            if logprobs:
                average_logprob = sum(logprobs) / len(logprobs)

            return {
                "text": transcript,
                "language": info.language if 'info' in locals() else "vi",
                "logprob": average_logprob
            }
        except Exception as e:
            print(f"[STT] Lỗi transcribe: {e}", flush=True)
            return {"text": "", "language": "vi", "logprob": None}