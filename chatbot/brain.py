import re
from threading import Lock

from llama_cpp import Llama

from chatbot.config import (
    MODEL_PATH,
    LLM_CONTEXT,
    LLM_BATCH,
    LLM_MAX_TOKENS,
    N_GPU_LAYERS,
    FLASH_ATTN,
    SYSTEM_PROMPT
)


class Brain:
    def __init__(self):
        print(f"Loading Qwen model: {MODEL_PATH}")
        print(f"n_gpu_layers={N_GPU_LAYERS}, n_ctx={LLM_CONTEXT} (chỉnh trong .env nếu thiếu VRAM)")

        self.model = Llama(
            model_path=MODEL_PATH,
            n_gpu_layers=N_GPU_LAYERS,
            n_ctx=LLM_CONTEXT,
            n_batch=LLM_BATCH,
            n_ubatch=128,
            flash_attn=FLASH_ATTN,  # False cho GTX 1660 Ti (Turing, thiếu Tensor Cores)
            verbose=True
        )

        self.lock = Lock()

    @staticmethod
    def clean_thinking(text: str) -> str:
        if not text:
            return ""

        text = re.sub(
            r"<think>.*?</think>",
            "",
            text,
            flags=re.DOTALL | re.IGNORECASE
        )

        text = re.sub(
            r"<think>.*$",
            "",
            text,
            flags=re.DOTALL | re.IGNORECASE
        )

        text = re.sub(
            r"</?think>",
            "",
            text,
            flags=re.IGNORECASE
        )

        return text.strip()

    def build_messages(
        self,
        user_text: str,
        history: list | None = None
    ):
        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ]

        history = history or []

        for item in history:
            if not isinstance(item, dict):
                continue

            role = item.get("role")
            content = item.get("content")

            if role not in ["user", "assistant"]:
                continue

            if not isinstance(content, str):
                continue

            if not content.strip():
                continue

            if role == "assistant":
                content = self.clean_thinking(content)

            messages.append({
                "role": role,
                "content": content
            })

        messages.append({
            "role": "user",
            "content": "/no_think\n" + user_text
        })

        return messages

    def stream(
        self,
        user_text: str,
        history: list | None = None
    ):
        messages = self.build_messages(
            user_text,
            history
        )

        with self.lock:
            response = self.model.create_chat_completion(
                messages=messages,
                temperature=0.3,
                top_p=0.8,
                max_tokens=LLM_MAX_TOKENS,
                stream=True,
                stop=["<|im_end|>"]
            )

            raw_text = ""

            for chunk in response:
                choices = chunk.get("choices", [])

                if not choices:
                    continue

                delta = choices[0].get("delta", {})
                token = delta.get("content", "")

                if not token:
                    continue

                raw_text += token

                answer = self.clean_thinking(raw_text)

                if answer:
                    yield answer