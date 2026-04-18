from typing import Literal

from app.core.interfaces import BaseLLM
from app.core.prompt_loader import load_prompt

from .base import BaseQueryTranslator
from .decomposition import MultiQueryTranslator, RagFusionTranslator, StepBackTranslator
from .hyde import HydeTranslator

QueryTranslationStrategyType = Literal["multi_query", "step_back", "rag_fusion", "hyde"]


class QueryTranslationFactory:
    @staticmethod
    def create(
        strategy: QueryTranslationStrategyType, llm: BaseLLM
    ) -> BaseQueryTranslator:
        if strategy == "multi_query":
            system_prompt = load_prompt("multi_query", category="system")
            user_prompt_template = load_prompt("multi_query", category="user")
            return MultiQueryTranslator(llm, system_prompt, user_prompt_template)

        elif strategy == "step_back":
            system_prompt = load_prompt("step_back", category="system")
            user_prompt_template = load_prompt("step_back", category="user")
            return StepBackTranslator(llm, system_prompt, user_prompt_template)

        elif strategy == "rag_fusion":
            system_prompt = load_prompt("rag_fusion", category="system")
            user_prompt_template = load_prompt("rag_fusion", category="user")
            return RagFusionTranslator(llm, system_prompt, user_prompt_template)

        elif strategy == "hyde":
            system_prompt = load_prompt("hyde", category="system")
            user_prompt_template = load_prompt("hyde", category="user")
            return HydeTranslator(llm, system_prompt, user_prompt_template)

        else:
            raise ValueError(f"Unknown query translation strategy: {strategy}")
