import os
import subprocess
import tempfile
from pathlib import Path

from chatbot.config import TEMP_DIR


def save_audio_bytes(audio_bytes: bytes, suffix: str = ".webm") -> str:
    fd, path = tempfile.mkstemp(
        suffix=suffix,
        dir=str(TEMP_DIR)
    )

    with os.fdopen(fd, "wb") as file:
        file.write(audio_bytes)

    return path


def convert_to_wav(input_path: str) -> str:
    output_path = str(
        Path(input_path).with_suffix(".wav")
    )

    command = [
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        "-ac",
        "1",
        "-ar",
        "16000",
        "-sample_fmt",
        "s16",
        output_path
    ]

    subprocess.run(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True
    )

    return output_path


def cleanup_files(*paths):
    for path in paths:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass