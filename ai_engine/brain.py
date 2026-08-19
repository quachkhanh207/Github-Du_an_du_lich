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

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        history: list | None = None,
        max_tokens: int | None = None
    ):
        """Async generator sinh token cho AI Orchestrator."""
        messages = self.build_messages(
            prompt,
            history,
            custom_system_prompt=system_prompt
        )

        import asyncio

        def _sync_generator():
            with self.lock:
                try:
                    response = self.model.create_chat_completion(
                        messages=messages,
                        temperature=0.3,
                        top_p=0.85,
                        max_tokens=max_tokens or LLM_MAX_TOKENS,
                        presence_penalty=0.5,
                        frequency_penalty=0.5,
                        repeat_penalty=1.15,
                        stream=True,
                        stop=["<|im_end|>", "[KẾT THÚC]", "[END]", "###"]
                    )
                    in_thinking = False
                    for chunk in response:
                        choices = chunk.get("choices", [])
                        if not choices:
                            continue
                        delta = choices[0].get("delta", {})
                        token = delta.get("content", "")
                        if not token:
                            continue

                        # Lọc thẻ <think> nếu có
                        if "<think>" in token:
                            in_thinking = True
                            continue
                        if "</think>" in token:
                            in_thinking = False
                            continue
                        if in_thinking:
                            continue

                        yield token

                except Exception as e:
                    print(f"[Brain] Lỗi inference: {e}", flush=True)
                    yield f"\n[Lỗi kết nối AI: {e}]"

        # Chuyển đổi sync generator sang async an toàn với executor
        loop = asyncio.get_event_loop()
        gen = _sync_generator()
        sentinel = object()

        def _fetch_next():
            return next(gen, sentinel)

        while True:
            try:
                tok = await loop.run_in_executor(None, _fetch_next)
                if tok is sentinel:
                    break
                yield tok
            except Exception as ex:
                print(f"[Brain] Stream token error: {ex}", flush=True)
                break

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        history: list | None = None,
        max_tokens: int | None = None
    ) -> str:
        """Sinh toàn bộ câu trả lời dạng chuỗi (Synchronous)."""
        messages = self.build_messages(
            prompt,
            history,
            custom_system_prompt=system_prompt
        )
        with self.lock:
            try:
                response = self.model.create_chat_completion(
                    messages=messages,
                    temperature=0.3,
                    top_p=0.85,
                    max_tokens=max_tokens or LLM_MAX_TOKENS,
                    presence_penalty=0.5,
                    frequency_penalty=0.5,
                    repeat_penalty=1.15,
                    stream=False,
                    stop=["<|im_end|>", "[KẾT THÚC]", "[END]", "###"]
                )
                raw_text = response["choices"][0]["message"]["content"]
                return self.clean_thinking(raw_text)
            except Exception as e:
                print(f"[Brain] Lỗi generate: {e}", flush=True)
                return "Xin lỗi bạn, tôi đang gặp gián đoạn tạm thời. Bạn vui lòng thử lại nhé!"