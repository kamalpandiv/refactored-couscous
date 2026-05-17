import json
from typing import Any, Dict, List, Optional, Union

import psycopg
from pgvector.psycopg import register_vector, register_vector_async
from psycopg.rows import dict_row
from psycopg.sql import SQL, Composed, Identifier

from app.core.config import settings
from app.core.interfaces import BaseVectorDB
from app.models.domain import DocumentChunk


class PGVectorDB(BaseVectorDB):
    def __init__(self):
        self.db_url = settings.DATABASE_URL
        self.dimension = settings.EMBEDDING_DIMENSION
        self.table_name = f"rag_vectors_{self.dimension}"
        print(f"rag_vectors_{self.dimension}")
        self._init_db()

    def _get_connection(self) -> psycopg.Connection[Any]:
        conn = psycopg.connect(self.db_url, row_factory=dict_row, autocommit=True)
        try:
            register_vector(conn)
        except psycopg.ProgrammingError:
            pass
        return conn

    async def _get_async_connection(self) -> psycopg.AsyncConnection[Any]:
        conn = await psycopg.AsyncConnection.connect(
            self.db_url, row_factory=dict_row, autocommit=True
        )
        await register_vector_async(conn)
        return conn

    def _init_db(self):
        """Sync init — only runs once at startup, fine to be blocking."""
        with psycopg.connect(self.db_url, autocommit=True) as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            register_vector(conn)
            conn.execute(
                SQL("""
                CREATE TABLE IF NOT EXISTS {table} (
                    id TEXT PRIMARY KEY,
                    text TEXT,
                    metadata JSONB,
                    embedding vector
                )
            """).format(table=Identifier(self.table_name))
            )
            conn.execute(
                SQL("""
                CREATE INDEX IF NOT EXISTS {idx_name}
                ON {table} USING hnsw (embedding vector_cosine_ops)
            """).format(
                    idx_name=Identifier(f"{self.table_name}_embedding_idx"),
                    table=Identifier(self.table_name),
                )
            )

    async def upsert(self, chunks: List[DocumentChunk], embeddings: List[List[float]]):
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks and embeddings must match!")

        async with await self._get_async_connection() as conn:
            async with conn.cursor() as cur:
                data = [
                    (chunk.id, chunk.text, json.dumps(chunk.metadata), embedding)
                    for chunk, embedding in zip(chunks, embeddings)
                ]
                await cur.executemany(
                    SQL("""
                        INSERT INTO {table} (id, text, metadata, embedding)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE
                        SET text = EXCLUDED.text,
                            metadata = EXCLUDED.metadata,
                            embedding = EXCLUDED.embedding
                    """).format(table=Identifier(self.table_name)),
                    data,
                )

    async def search(
        self,
        query_vector: List[float],
        top_k: int,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[DocumentChunk]:
        base_query: List[Union[SQL, Composed]] = [
            SQL(
                "SELECT id, text, metadata, 1 - (embedding <=> %s::vector) AS score FROM {table}"
            ).format(table=Identifier(self.table_name))
        ]
        params: List[Any] = [query_vector]

        if filters and "source" in filters:
            source_file = filters["source"].get("$eq")
            if source_file:
                base_query.append(SQL("WHERE metadata->>'source' = %s"))
                params.append(source_file)

        base_query.append(SQL("ORDER BY embedding <=> %s::vector LIMIT %s"))
        params.extend([query_vector, top_k])

        final_query = SQL(" ").join(base_query)

        async with await self._get_async_connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(final_query, params)
                rows = await cur.fetchall()

                return [
                    DocumentChunk(
                        id=str(row["id"]),
                        text=str(row["text"]),
                        metadata=row["metadata"],
                        score=float(row["score"]),
                    )
                    for row in rows
                ]
