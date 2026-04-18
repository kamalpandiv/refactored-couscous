from typing import List

from .base import BaseQueryTranslator


class HydeTranslator(BaseQueryTranslator):
    async def translate(self, query: str) -> List[str]:
        prompt = self.user_prompt_template.format(query=query)

        hypothetical_doc = await self.llm.generate_response(
            prompt=prompt, context="", system_prompt=self.system_prompt
        )

        return [hypothetical_doc.strip()]
