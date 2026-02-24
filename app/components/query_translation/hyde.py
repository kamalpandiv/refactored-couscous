from typing import List

from .base import BaseQueryTranslator


class HydeTranslator(BaseQueryTranslator):
    async def translate(self, query: str) -> List[str]:
        system_task = "You are a helpful assistant. Write a hypothetical scientific paper passage to answer the question."

        prompt = f"""
        Question: {query}
        Passage:
        """

        hypothetical_doc = await self.llm.generate_response(
            prompt=prompt, context="", system_prompt=system_task
        )

        return [hypothetical_doc.strip()]
