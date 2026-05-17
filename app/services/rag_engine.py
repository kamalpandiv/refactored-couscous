import asyncio
import time
from typing import Dict, List, Optional

from app.components.query_translation import (
    QueryTranslationFactory,
    QueryTranslationStrategyType,
)
from app.core.config import settings
from app.core.interfaces import BaseEmbedder, BaseLLM, BaseVectorDB
from app.models.domain import DocumentChunk


class RAGEngine:
    def __init__(
        self,
        vector_db: BaseVectorDB,
        embedder: BaseEmbedder,
        llm: BaseLLM,
        system_prompt: str = "",
    ):
        self.vector_db = vector_db
        self.embedder = embedder
        self.llm = llm
        self.system_prompt = system_prompt

    async def _embed_and_search(
        self,
        query: str,
        filters: dict,
    ) -> List[DocumentChunk]:
        """Embed a single query and search — designed to run concurrently."""
        vector = await self.embedder.embed_text(query)
        return await self.vector_db.search(
            vector, top_k=settings.TOP_K, filters=filters
        )

    async def answer_question(
        self,
        query: str,
        file_filter: Optional[str] = None,
        translation_strategy: Optional[QueryTranslationStrategyType] = None,
        custom_system_prompt: Optional[str] = None,
    ) -> Dict:
        """
        Orchestrates: Translate -> Embed -> Retrieve -> Augment -> Generate
        """
        start_time = time.time()
        print("\n[RAG Engine] Starting query pipeline...")
        print(f" ↳ Question: '{query}'")

        # 1. Query Translation + Final Answer — run concurrently when possible
        queries_to_embed = [query]

        if translation_strategy:
            print(f"Applying translation strategy: {translation_strategy}...")
            translator = QueryTranslationFactory.create(
                strategy=translation_strategy, llm=self.llm
            )
            queries_to_embed = await translator.translate(query)
            print(f" ↳ Generated {len(queries_to_embed)} queries to search:")
            for i, q in enumerate(queries_to_embed):
                print(f"        {i + 1}. {q}")
        else:
            print("No translation strategy applied. Using raw query.")
        print(f"[TIMER] Translation:   {time.time() - start_time:.2f}s")
        start_time = time.time()

        # 2. Construct Filter
        db_filters: dict = {}
        if file_filter:
            db_filters = {"source": {"$eq": file_filter}}
            print(f"Filter applied: searching only in '{file_filter}'")

        # 3. Embed + Search ALL queries concurrently ← key optimization
        print("Retrieving context from Vector DB...")
        results = await asyncio.gather(
            *[self._embed_and_search(q, db_filters) for q in queries_to_embed]
        )
        print(f"[TIMER] Embed+Search:  {time.time() - start_time:.2f}s")
        start_time = time.time()

        # Flatten + deduplicate
        all_chunks = [chunk for batch in results for chunk in batch]
        unique_chunks = list({chunk.id: chunk for chunk in all_chunks}.values())
        print(
            f"      ↳ Found {len(unique_chunks)} unique context chunks across all queries."
        )

        # 4. Build context
        context_text = "\n\n".join(
            f"Source ({chunk.metadata.get('source', 'Unknown')}): {chunk.text}"
            for chunk in unique_chunks
        )

        # 5. Generate answer
        selected_prompt = custom_system_prompt or self.system_prompt
        print(f"Generating final response using LLM ({settings.LLM_MODEL})...")
        answer = await self.llm.generate_response(
            prompt=query,
            context=context_text,
            system_prompt=selected_prompt,
        )
        print(f"[TIMER] LLM Generate:  {time.time() - start_time:.2f}s")
        print(f"[TIMER] Total:         {time.time() - start_time:.2f}s")

        duration = time.time() - start_time
        print(f"[RAG Engine] Pipeline complete in {duration:.2f} seconds.\n")

        return {
            "answer": answer,
            "citations": [c.metadata for c in unique_chunks],
            "generated_queries": queries_to_embed,
        }
