from typing import Optional

from openai import OpenAI

from app.core.config import settings
from app.core.interfaces import BaseLLM


class OpenAILLM(BaseLLM):
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.LLM_MODEL

    async def generate_response(
        self,
        prompt: str,
        context: str,
        system_prompt: Optional[str] = None,  # NEW: Allow override
    ) -> str:

        # Default Strict RAG Prompt (used if no override is provided)
        if system_prompt is None:
            system_prompt = (
                "You are a precise and helpful AI assistant designed to answer questions "
                "based strictly on the provided context."
                "\n\n"
                "Guidelines:"
                "\n1. **Use ONLY the context provided** to answer the user's question."
                "\n2. **Do NOT use outside knowledge**."
                "\n3. If the answer cannot be found in the context, clearly state: "
                "'I cannot answer this based on the provided information.'"
            )

        user_content = f"Context:\n{context}\n\nQuestion: {prompt}"

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=settings.LLM_TEMP
            if not system_prompt
            else 0.7,  # Higher temp for creative tasks
        )
        return response.choices[0].message.content
