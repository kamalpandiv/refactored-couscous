import time
import uuid
from typing import List

from app.components.chunking.factory import ChunkingFactory
from app.components.embedders.langchain_wrapper import LangChainEmbeddingsWrapper
from app.core.config import settings
from app.core.interfaces import BaseEmbedder, BaseVectorDB
from app.models.domain import DocumentChunk


class IngestionService:
    def __init__(self, embedder: BaseEmbedder, vector_db: BaseVectorDB):
        self.embedder = embedder
        self.vector_db = vector_db

    async def ingest_texts(self, texts: List[str], source_name: str):
        start_time = time.time()
        print(f"[Start] Ingesting {len(texts)} texts from: {source_name}")

        # 1. Chunking
        print(f"Chunking strategy: {settings.CHUNKING_STRATEGY}...")

        lc_embedder = LangChainEmbeddingsWrapper(self.embedder)
        chunker = ChunkingFactory.create(
            strategy=settings.CHUNKING_STRATEGY, embedder=lc_embedder, token_safe=True
        )

        all_chunks: List[DocumentChunk] = []
        total_tokens = 0

        for text in texts:
            raw_chunks = chunker.chunk(text)
            print(f" ↳ Generated {len(raw_chunks)} chunks for a text block.")

            for i, chunk_text in enumerate(raw_chunks):
                # We can create a readable ID like "cpumemory.pdf-chunk-0"
                # or a guaranteed unique one with uuid. Let's use a combination for easy debugging!
                chunk_id = f"{source_name}-chunk-{i}-{str(uuid.uuid4())[:8]}"

                doc_chunk = DocumentChunk(
                    id=chunk_id,
                    text=chunk_text,
                    metadata={
                        "source": source_name,
                        "chunk_index": i,
                        "strategy": settings.CHUNKING_STRATEGY,
                    },
                )
                all_chunks.append(doc_chunk)
                total_tokens += len(chunk_text.split())

        if not all_chunks:
            print("[Error] No chunks generated.")
            return

        print(f"Chunking complete. Total chunks: {len(all_chunks)}")

        # 2. Embedding
        print(f"Generating Embeddings (Batch Size: {settings.BATCH_SIZE})...")
        vectors = []

        total = len(all_chunks)
        for i in range(0, total, settings.BATCH_SIZE):
            batch = all_chunks[i : i + settings.BATCH_SIZE]
            batch_texts = [c.text for c in batch]

            batch_vectors = await self.embedder.embed_batch(batch_texts)
            vectors.extend(batch_vectors)

            print(
                f" ↳ Embedded {min(i + settings.BATCH_SIZE, total)}/{total} chunks..."
            )

        print(f"[Debug] Chunks count: {len(all_chunks)}, Vectors count: {len(vectors)}")

        # 3. Storage
        print("Upserting to Vector DB...")
        await self.vector_db.upsert(all_chunks, vectors)

        duration = time.time() - start_time
        print(f"Done] Ingestion finished in {duration:.2f}s.")
