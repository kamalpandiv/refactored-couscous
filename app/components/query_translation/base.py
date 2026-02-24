from abc import ABC, abstractmethod
from typing import List

from app.core.interfaces import BaseLLM


class BaseQueryTranslator(ABC):
    def __init__(self, llm: BaseLLM):
        self.llm = llm

    @abstractmethod
    async def translate(self, query: str) -> List[str]:
        """
        Translates a single user query into a list of queries or
        hypothetical documents.
        """
        pass
