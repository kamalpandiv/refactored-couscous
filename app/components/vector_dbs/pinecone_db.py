import time
from typing import Dict, List

from pinecone import ServerlessSpec
from pinecone.grpc import PineconeGRPC as Pinecone

from app.core.config import settings
from app.core.interfaces import BaseVectorDB
from app.models.domain import DocumentChunk


class PineconeDB(BaseVectorDB):
    def __init__(self):
        # 1. Use the new PINECONE_API_KEY from settings
        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)

        # 2. Update to new config variable name: PINECONE_INDEX_NAME
        self.index_name = settings.PINECONE_INDEX_NAME

        self._initialize_index()
        self.index = self.pc.Index(self.index_name)

    def _initialize_index(self):
        # check if index exists
        existing_indexes = [i.name for i in self.pc.list_indexes()]

        if self.index_name not in existing_indexes:
            # 3. Use unified settings for Cloud and Region
            spec = ServerlessSpec(
                cloud=settings.PINECONE_CLOUD, region=settings.PINECONE_REGION
            )

            self.pc.create_index(
                name=self.index_name,
                # 4. Use the unified EMBEDDING_DIMENSION (e.g. 1536 or 512)
                dimension=settings.EMBEDDING_DIMENSION,
                metric="cosine",  # Recommend 'cosine' over 'dotproduct' for OpenAI v3
                spec=spec,
            )
            # Wait a moment for the index to be ready
            while not self.pc.describe_index(self.index_name).status["ready"]:
                time.sleep(1)

    async def upsert(self, chunks: List[DocumentChunk], embeddings: List[List[float]]):

        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks and embeddings must match!")

        vectors = []

        # Loop through both lists at the same time using zip()
        for chunk, embedding in zip(chunks, embeddings):
            # Ensure metadata is a flat dict (Pinecone requirement)
            meta = chunk.metadata.copy() if chunk.metadata else {}
            meta["text"] = chunk.text

            # Pass the paired 'embedding' here, not 'chunk.vector'
            vectors.append((chunk.id, embedding, meta))

        # Upsert in batches
        self.index.upsert(vectors=vectors)

    async def search(
        self, query_vector: List[float], top_k: int, filters: Dict = None
    ) -> List[DocumentChunk]:
        # Validate dimension match
        if len(query_vector) != settings.EMBEDDING_DIMENSION:
            raise ValueError(
                f"Query vector size {len(query_vector)} does not match Index dimension {settings.EMBEDDING_DIMENSION}"
            )

        res = self.index.query(
            vector=query_vector, top_k=top_k, include_metadata=True, filter=filters
        )

        results = []
        for match in res["matches"]:
            # Safely get text, defaulting to empty string if missing
            text_content = match["metadata"].get("text", "")

            results.append(
                DocumentChunk(
                    id=match["id"],
                    text=text_content,
                    metadata=match["metadata"],
                    score=match["score"],
                )
            )
        print("[Pinecone Search]")
        return results
