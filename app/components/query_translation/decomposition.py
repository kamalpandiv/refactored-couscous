from typing import List

from .base import BaseQueryTranslator


class MultiQueryTranslator(BaseQueryTranslator):
    async def translate(self, query: str) -> List[str]:
        prompt = self.user_prompt_template.format(query=query)

        response = await self.llm.generate_response(
            prompt=prompt, context="", system_prompt=self.system_prompt
        )

        return [q.strip() for q in response.split("\n") if q.strip()]


class StepBackTranslator(BaseQueryTranslator):
    async def translate(self, query: str) -> List[str]:
        prompt = self.user_prompt_template.format(query=query)

        step_back_question = await self.llm.generate_response(
            prompt=prompt, context="", system_prompt=self.system_prompt
        )

        return [query, step_back_question.strip()]


class RagFusionTranslator(BaseQueryTranslator):
    async def translate(self, query: str) -> List[str]:
        prompt = self.user_prompt_template.format(query=query)

        response = await self.llm.generate_response(
            prompt=prompt, context="", system_prompt=self.system_prompt
        )

        return [q.strip() for q in response.split("\n") if q.strip()]
