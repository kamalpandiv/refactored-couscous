from typing import Literal

from app.core.interfaces import BaseLLM

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
            return MultiQueryTranslator(llm)

        elif strategy == "step_back":
            return StepBackTranslator(llm)

        elif strategy == "rag_fusion":
            return RagFusionTranslator(llm)

        elif strategy == "hyde":
            return HydeTranslator(llm)

        else:
            raise ValueError(f"Unknown query translation strategy: {strategy}")
