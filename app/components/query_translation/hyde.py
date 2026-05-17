from typing import List

from .base import BaseQueryTranslator


class HydeTranslator(BaseQueryTranslator):
    async def translate(self, query: str) -> List[str]:
        prompt = self.user_prompt_template.format(query=query)

        hypothetical_doc = await self.llm.complete(
            prompt=prompt, system=self.system_prompt
        )

        return [hypothetical_doc.content.strip()]
