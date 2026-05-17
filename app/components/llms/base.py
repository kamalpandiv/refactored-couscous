from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator


@dataclass
class LLMResponse:
    content: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0


class BaseLLMProvider(ABC):

    @abstractmethod
    async def complete(self, prompt: str, system: str = "") -> LLMResponse: ...

    @abstractmethod
    def stream(self, prompt: str, system: str = "") -> AsyncIterator[str]:
        # returning an AsyncIterator
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str: ...