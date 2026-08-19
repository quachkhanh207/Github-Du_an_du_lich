import re
import torch

from faster_whisper import WhisperModel


from api_server.config import STT_DEVICE


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

        print(f"Loading Whisper: {model_size} on {device_choice} ({compute_type})")

        self.model = WhisperModel(
            model_size,
            device=device_choice,
            compute_type=compute_type
        )

    @staticmethod
    def normalize(text: str) -> str:
        if not text:
            return ""

        text = re.sub(r"\s+", " ", text.strip())

        replacements = {
            " đà nẵng ": " Đà Nẵng ",
            " hội an ": " Hội An ",
            " hà nội ": " Hà Nội ",
            " hồ chí minh ": " Hồ Chí Minh ",
            " tphcm ": " Thành phố Hồ Chí Minh ",
            " tp hcm ": " Thành phố Hồ Chí Minh "
        }

        padded = f" {text.lower()} "

        for old, new in replacements.items():
            padded = padded.replace(old, new)

        text = padded.strip()

        if text:
            text = text[0].upper() + text[1:]

        return text

    def transcribe_fast(self, audio_path: str) -> dict:
        segments, info = self.model.transcribe(
            audio_path,
            language=self.language,
            task="transcribe",
            beam_size=1,
            best_of=1,
            temperature=0.0,
            condition_on_previous_text=False,
            vad_filter=True,
            vad_parameters={
                "min_silence_duration_ms": 500,
                "speech_pad_ms": 200,
                "min_speech_duration_ms": 250
            },
            word_timestamps=False
        )

        texts = []

        for segment in segments:
            text = segment.text.strip()

            if text:
                texts.append(text)

        transcript = self.normalize(" ".join(texts))

        return {
            "text": transcript,
            "language": info.language,
            "logprob": None
        }

    def transcribe(self, audio_path: str) -> dict:
        segments, info = self.model.transcribe(
            audio_path,
            language=self.language,
            task="transcribe",
            beam_size=3,
            best_of=3,
            temperature=0.0,
            condition_on_previous_text=False,
            vad_filter=True,
            vad_parameters={
                "min_silence_duration_ms": 700,
                "speech_pad_ms": 300,
                "min_speech_duration_ms": 250
            },
            no_speech_threshold=0.6,
            log_prob_threshold=-1.0,
            compression_ratio_threshold=2.4,
            word_timestamps=False
        )

        segments = list(segments)

        texts = []
        logprobs = []

        for segment in segments:
            text = segment.text.strip()

            if not text:
                continue

            if segment.avg_logprob is not None:
                if segment.avg_logprob < -1.2:
                    continue

                logprobs.append(segment.avg_logprob)

            texts.append(text)

        transcript = self.normalize(" ".join(texts))

        average_logprob = None

        if logprobs:
            average_logprob = sum(logprobs) / len(logprobs)

        return {
            "text": transcript,
            "language": info.language,
            "logprob": average_logprob
        }