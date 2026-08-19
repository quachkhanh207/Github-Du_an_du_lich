import re
import sys
from threading import Lock

from llama_cpp import Llama

from api_server.config import (
    MODEL_PATH,
    LLM_CONTEXT,
    LLM_BATCH,
    LLM_MAX_TOKENS,
    N_GPU_LAYERS,
    FLASH_ATTN,
    SYSTEM_PROMPT
)

# Fix encoding tren Windows console
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


class Brain:
    def __init__(self):
        print(f"[Brain] Loading model: {MODEL_PATH}", flush=True)
        print(f"[Brain] n_gpu_layers={N_GPU_LAYERS}, n_ctx={LLM_CONTEXT}", flush=True)

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

    MAX_HISTORY_PAIRS = 6

    def _trim_history(self, history: list) -> list:
        """Chỉ giữ lại MAX_HISTORY_PAIRS cặp hội thoại gần nhất để tránh tràn KV cache."""
        if not history:
            return []

        valid = []
        for item in history:
            if not isinstance(item, dict):
                continue
            role = item.get("role")
            content = item.get("content")
            if role not in ("user", "assistant"):
                continue
            if not isinstance(content, str) or not content.strip():
                continue
            valid.append(item)

        max_items = self.MAX_HISTORY_PAIRS * 2
        if len(valid) > max_items:
            valid = valid[-max_items:]

        return valid

    def build_messages(
        self,
        user_text: str,
        history: list | None = None,
        custom_system_prompt: str | None = None
    ):
        messages = [
            {
                "role": "system",
                "content": custom_system_prompt or SYSTEM_PROMPT
            }
        ]

        trimmed = self._trim_history(history or [])

        for item in trimmed:
            role = item["role"]
            content = item["content"]

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
        history: list | None = None,
        custom_system_prompt: str | None = None
    ):
        messages = self.build_messages(
            user_text,
            history,
            custom_system_prompt=custom_system_prompt
        )

        with self.lock:
            try:
                response = self.model.create_chat_completion(
                    messages=messages,
                    temperature=0.2,
                    top_p=0.85,
                    max_tokens=LLM_MAX_TOKENS,
                    presence_penalty=0.6,
                    frequency_penalty=0.6,
                    repeat_penalty=1.15,
                    stream=True,
                    stop=["<|im_end|>", "[KẾT THÚC]", "[END]", "###"]
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

                final_answer = self.clean_thinking(raw_text)
                if not final_answer and raw_text.strip():
                    final_answer = re.sub(r"</?think>", "", raw_text).strip()
                if final_answer:
                    yield final_answer

            except Exception as e:
                err_msg = str(e)
                print(f"[Brain] Lỗi trong stream(): {err_msg}", flush=True)
                if "context" in err_msg.lower() or "kv" in err_msg.lower():
                    yield "Xin lỗi, lịch sử hội thoại quá dài. Vui lòng làm mới cuộc trò chuyện."
                else:
                    yield f"Tôi đang gặp sự cố khi xử lý câu hỏi này. Bạn vui lòng thử lại nhé! (Chi tiết: {err_msg})"