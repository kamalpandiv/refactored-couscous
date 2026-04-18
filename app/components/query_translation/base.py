from abc import ABC, abstractmethod
from typing import List

from app.core.interfaces import BaseLLM


class BaseQueryTranslator(ABC):
    def __init__(self, llm: BaseLLM, system_prompt: str, user_prompt_template: str):
        self.llm = llm
        self.system_prompt = system_prompt
        self.user_prompt_template = user_prompt_template

    @abstractmethod
    async def translate(self, query: str) -> List[str]:
        """
        Translates a single user query into a list of queries or
        hypothetical documents.
        """
        pass
