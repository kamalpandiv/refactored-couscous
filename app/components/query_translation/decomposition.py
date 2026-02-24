from typing import List

from .base import BaseQueryTranslator


class MultiQueryTranslator(BaseQueryTranslator):
    async def translate(self, query: str) -> List[str]:
        system_task = "You are an AI language model assistant. Your task is to generate 3 different versions of the given user question."

        prompt = f"""
        Original question: {query}
        Provide these alternative questions separated by newlines.
        """

        response = await self.llm.generate_response(
            prompt=prompt, context="", system_prompt=system_task
        )

        return [q.strip() for q in response.split("\n") if q.strip()]


class StepBackTranslator(BaseQueryTranslator):
    async def translate(self, query: str) -> List[str]:
        system_task = "You are an expert at world knowledge. Your task is to paraphrase a question to a more generic step-back questions."

        prompt = f"""
        Original Question: {query}
        Step-back Question:
        """

        step_back_question = await self.llm.generate_response(
            prompt=prompt, context="", system_prompt=system_task
        )

        return [query, step_back_question.strip()]


class RagFusionTranslator(BaseQueryTranslator):
    async def translate(self, query: str) -> List[str]:
        system_task = "You are a helpful assistant that generates multiple search queries based on a single input query."

        prompt = f"""
        Generate 4 search queries related to: {query}
        OUTPUT (4 queries):
        """

        response = await self.llm.generate_response(
            prompt=prompt, context="", system_prompt=system_task
        )

        return [q.strip() for q in response.split("\n") if q.strip()]
