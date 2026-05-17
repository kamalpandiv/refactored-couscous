import asyncio
import json
from typing import AsyncIterator

import httpx
from langchain_community.llms.llamacpp import LlamaCpp
from langchain_core.callbacks import CallbackManager, StreamingStdOutCallbackHandler

from app.components.llms.base import BaseLLMProvider, LLMResponse
from app.core.config import settings


class LlamaCppProvider(BaseLLMProvider):
    def __init__(self):
        self.remote_url = getattr(settings, "REMOTE_LLAMACPP_URL", None)
        self.timeout = httpx.Timeout(60.0, connect=10.0)

        if self.remote_url:
            self.remote_url = self.remote_url.rstrip("/")
            print(
                f"[LlamaCppProvider] Remote URL found: {self.remote_url}. Testing connection..."
            )

            if self._check_connection():
                print(" ↳Connection successful! Skipping local RAM allocation.")
                self._llm = None
            else:
                print(" ↳Connection failed! Remote server is down or unreachable.")
                print(" ↳Falling back: Loading local model into RAM...")
                self.remote_url = None 
                self._init_local_llm()
        else:
            print("[LlamaCppProvider] No remote URL configured.")
            self._init_local_llm()

    def _init_local_llm(self):
        print(f"Loading local model into RAM: {settings.LOCAL_MODEL}")
        self._llm = LlamaCpp(
            model_path=settings.LOCAL_MODEL,
            temperature=settings.LLM_TEMP,
            max_tokens=2000,
            n_ctx=4000,
            stop=["<|im_end|>", "<|im_start|>", " assistant"],
            top_p=0.9,
            callback_manager=CallbackManager([StreamingStdOutCallbackHandler()]),
            verbose=settings.DEBUG,
            n_gpu_layers=-1,
        )

    def _check_connection(self) -> bool:
        """Performs a synchronous ping to the llama.cpp server health endpoint."""
        try:
            # We use a strict, short timeout (e.g., 3 seconds) for startup health checks
            with httpx.Client(timeout=3.0) as client:
                response = client.get(f"{self.remote_url}/health")

                # llama.cpp server returns {"status": "ok"} when healthy
                if response.status_code == 200:
                    status_data = response.json()
                    return status_data.get("status") == "ok"
                return False
        except (httpx.RequestError, httpx.HTTPStatusError, json.JSONDecodeError):
            return False

    @property
    def provider_name(self) -> str:
        if self.remote_url:
            return f"remote-llamacpp/{self.remote_url}"
        return f"llamacpp/{settings.LOCAL_MODEL}"

    def _build_prompt(self, prompt: str, system: str) -> str:
        if system:
            return (
                f"<|im_start|>system\n{system}<|im_end|>\n"
                f"<|im_start|>user\n{prompt}<|im_end|>\n"
                f"<|im_start|>assistant\n"
            )
        return f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"

    async def complete(self, prompt: str, system: str = "") -> LLMResponse:
        full_prompt = self._build_prompt(prompt, system)

        # --- REMOTE PATH ---
        if self.remote_url:
            payload = {
                "prompt": full_prompt,
                "temperature": settings.LLM_TEMP,
                "n_predict": 2000,
                "stop": ["<|im_end|>", "<|im_start|>", " assistant"],
            }
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.remote_url}/completion", json=payload
                )
                response.raise_for_status()
                content = response.json()["content"]
                return LLMResponse(content=content, model="remote-llamacpp")

        # --- LOCAL PATH ---
        if self._llm is None:
            raise RuntimeError("LlamaCpp local engine was not initialized.")

        loop = asyncio.get_event_loop()
        content = await loop.run_in_executor(
            None,
            lambda: self._llm.invoke(full_prompt),
        )

        if not content:
            raise ValueError("LlamaCpp returned an empty response.")

        return LLMResponse(
            content=content,
            model=settings.LOCAL_MODEL,
        )

    async def stream(self, prompt: str, system: str = "") -> AsyncIterator[str]:
        full_prompt = self._build_prompt(prompt, system)

        # --- REMOTE PATH ---
        if self.remote_url:
            payload = {
                "prompt": full_prompt,
                "temperature": settings.LLM_TEMP,
                "n_predict": 2000,
                "stop": ["<|im_end|>", "<|im_start|>", " assistant"],
                "stream": True,
            }
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST", f"{self.remote_url}/completion", json=payload
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            try:
                                chunk_data = json.loads(line[6:])
                                content = chunk_data.get("content", "")
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                continue
            return

        # --- LOCAL PATH ---
        if self._llm is None:
            raise RuntimeError("LlamaCpp local engine was not initialized.")

        loop = asyncio.get_event_loop()
        queue: asyncio.Queue[str | None] = asyncio.Queue()

        def _stream_to_queue():
            try:
                for chunk in self._llm.stream(full_prompt):
                    loop.call_soon_threadsafe(queue.put_nowait, chunk)
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, None)

        loop.run_in_executor(None, _stream_to_queue)

        while True:
            chunk = await queue.get()
            if chunk is None:
                break
            yield chunk
