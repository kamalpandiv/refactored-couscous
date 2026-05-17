import asyncio
import json
import os
from typing import AsyncIterator

import httpx
from langchain_community.llms.llamacpp import LlamaCpp
from langchain_core.callbacks import CallbackManager, StreamingStdOutCallbackHandler

from app.components.llms.base import BaseLLMProvider, LLMResponse
from app.core.config import settings


class LlamaCppProvider(BaseLLMProvider):
    def __init__(self):
        self.remote_url = getattr(settings, "REMOTE_LLAMACPP_URL", None)

        # Pull timeouts dynamically from settings
        remote_timeout = getattr(settings, "LLM_REMOTE_TIMEOUT", 60.0)
        connect_timeout = getattr(settings, "LLM_REMOTE_CONNECT_TIMEOUT", 10.0)
        self.timeout = httpx.Timeout(remote_timeout, connect=connect_timeout)

        # Centrally defined generation config to share between remote payloads and local setups
        self.max_tokens = getattr(settings, "LLM_MAX_TOKENS", 2000)
        self.stop_sequences = getattr(
            settings, "LLM_STOP_SEQUENCES", ["<|im_end|>", "<|im_start|>", " assistant"]
        )

        if self.remote_url:
            self.remote_url = self.remote_url.rstrip("/")
            print(
                f"[LlamaCppProvider] Remote URL found: {self.remote_url}. Testing connection..."
            )

            if self._check_connection():
                print(" ↳ Connection successful! Skipping local RAM allocation.")
                self._llm = None
            else:
                print(" ↳ Connection failed! Remote server is down or unreachable.")
                print(" ↳ Falling back: Loading local model into RAM...")
                self.remote_url = None
                self._init_local_llm()
        else:
            print("[LlamaCppProvider] No remote URL configured.")
            self._init_local_llm()

    def _init_local_llm(self):
        if not settings.LOCAL_MODEL or not os.path.exists(settings.LOCAL_MODEL):
            raise FileNotFoundError(
                f"Initialization Failed: Remote server was unreachable and "
                f"local model file does not exist at path: '{settings.LOCAL_MODEL}'"
            )

        print(f"Loading local model into RAM: {settings.LOCAL_MODEL}")

        # Pull local-specific constraints safely out of global configs
        n_ctx = getattr(settings, "LLM_N_CTX", 4000)
        top_p = getattr(settings, "LLM_TOP_P", 0.9)
        n_gpu_layers = getattr(settings, "LLM_N_GPU_LAYERS", -1)

        self._llm = LlamaCpp(
            model_path=settings.LOCAL_MODEL,
            temperature=settings.LLM_TEMP,
            max_tokens=self.max_tokens,
            n_ctx=n_ctx,
            stop=self.stop_sequences,
            top_p=top_p,
            callback_manager=CallbackManager([StreamingStdOutCallbackHandler()]),
            verbose=settings.DEBUG,
            n_gpu_layers=n_gpu_layers,
        )

    def _check_connection(self) -> bool:
        """Performs a synchronous ping to the llama.cpp server health endpoint."""
        health_timeout = getattr(settings, "LLM_HEALTH_CHECK_TIMEOUT", 3.0)
        try:
            with httpx.Client(timeout=health_timeout) as client:
                response = client.get(f"{self.remote_url}/health")
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
        # Prompt wrappers can also be moved to settings if you shift from ChatML to Llama-3/Alpaca formats later
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
                "n_predict": self.max_tokens,
                "stop": self.stop_sequences,
            }
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                try:
                    response = await client.post(
                        f"{self.remote_url}/completion", json=payload
                    )
                    response.raise_for_status()
                    content = response.json()["content"]
                    return LLMResponse(content=content, model="remote-llamacpp")
                except httpx.HTTPStatusError as e:
                    server_error_text = ""
                    try:
                        server_error_text = f" | Server Message: {e.response.json()['error']['message']}"
                    except Exception:
                        server_error_text = f" | Details: {e.response.text}"

                    print(
                        f"[LlamaCppProvider] Remote API Error: {e}{server_error_text}"
                    )
                    raise RuntimeError(
                        f"Remote LLM Server returned error status {e.response.status_code}.{server_error_text}"
                    )

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

        return LLMResponse(content=content, model=settings.LOCAL_MODEL)

    async def stream(self, prompt: str, system: str = "") -> AsyncIterator[str]:
        full_prompt = self._build_prompt(prompt, system)

        # --- REMOTE PATH ---
        if self.remote_url:
            payload = {
                "prompt": full_prompt,
                "temperature": settings.LLM_TEMP,
                "n_predict": self.max_tokens,
                "stop": self.stop_sequences,
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

        # 1. Capture the engine in a local variable to satisfy the type checker's narrow scope
        local_llm = self._llm

        loop = asyncio.get_event_loop()
        queue: asyncio.Queue[str | None] = asyncio.Queue()

        def _stream_to_queue():
            try:
                # 2. Reference the guaranteed local variable instead of self._llm
                for chunk in local_llm.stream(full_prompt):
                    loop.call_soon_threadsafe(queue.put_nowait, chunk)
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, None)

        loop.run_in_executor(None, _stream_to_queue)

        while True:
            chunk = await queue.get()
            if chunk is None:
                break
            yield chunk
