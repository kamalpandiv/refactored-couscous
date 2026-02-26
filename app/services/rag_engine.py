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
    def __init__(self, vector_db: BaseVectorDB, embedder: BaseEmbedder, llm: BaseLLM):
        self.vector_db = vector_db
        self.embedder = embedder
        self.llm = llm

    async def answer_question(
        self,
        query: str,
        file_filter: Optional[str] = None,
        translation_strategy: Optional[QueryTranslationStrategyType] = None,
    ) -> Dict:
        """
        Orchestrates: Translate -> Embed -> Retrieve -> Augment -> Generate
        """
        start_time = time.time()
        print("\n[RAG Engine] Starting query pipeline...")
        print(f" ↳ Question: '{query}'")

        # 1. Query Translation (Optional)
        queries_to_embed = [query]  # Default to raw query

        if translation_strategy:
            print(f"Applying translation strategy: {translation_strategy}...")
            translator = QueryTranslationFactory.create(
                strategy=translation_strategy, llm=self.llm
            )
            queries_to_embed = await translator.translate(
                query
            )  # the embedded new query are added to new list
            print(f" ↳ Generated {len(queries_to_embed)} queries to search:")
            for i, q in enumerate(queries_to_embed):
                print(f"        {i + 1}. {q}")
        else:
            print("No translation strategy applied. Using raw query.")

        # 2. Construct Filter
        db_filters = {}
        if file_filter:
            db_filters = {"source": {"$eq": file_filter}}
            print(f"Filter applied: searching only in '{file_filter}'")

        # 3. Retrieve (Multi-Query Support)
        print("Retrieving context from Vector DB...")
        all_retrieved_chunks: List[DocumentChunk] = []

        for q in queries_to_embed:
            query_vector = await self.embedder.embed_text(q)
            chunks = await self.vector_db.search(
                query_vector, top_k=settings.TOP_K, filters=db_filters
            )
            all_retrieved_chunks.extend(chunks)

        # Deduplicate chunks based on ID
        unique_chunks = {chunk.id: chunk for chunk in all_retrieved_chunks}.values()
        print(
            f"      ↳ Found {len(unique_chunks)} unique context chunks across all queries."
        )

        # 4. Augmentation (Context Construction)
        context_text = "\n\n".join(
            [
                f"Source ({chunk.metadata.get('source', 'Unknown')}): {chunk.text}"
                for chunk in unique_chunks
            ]
        )

        print("\n" + "=" * 40)
        print("CONTEXT GIVEN TO LLM:")
        print(context_text)
        print("=" * 40 + "\n")

        # 5. Generation (Final Answer)
        print(f"Generating final response using LLM ({settings.LLM_MODEL})...")
        answer = await self.llm.generate_response(prompt=query, context=context_text)

        duration = time.time() - start_time
        print(f"[RAG Engine] Pipeline complete in {duration:.2f} seconds.\n")

        # 6. Return Answer + Citations
        return {
            "answer": answer,
            "citations": [c.metadata for c in unique_chunks],
            "generated_queries": queries_to_embed,
        }
