import json
from typing import Any, Dict, List, Optional, Union

import psycopg
from pgvector.psycopg import register_vector
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
        conn = psycopg.connect(self.db_url, row_factory=dict_row, autocommit=True)  # type: ignore
        try:
            register_vector(conn)
        except psycopg.ProgrammingError:
            pass
        return conn

    def _init_db(self):
        """Creates the vector extension and the table."""
        with psycopg.connect(self.db_url, autocommit=True) as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            register_vector(conn)

            create_table_query = SQL("""
                CREATE TABLE IF NOT EXISTS {table} (
                    id TEXT PRIMARY KEY,
                    text TEXT,
                    metadata JSONB,
                    embedding vector
                )
            """).format(table=Identifier(self.table_name))
            conn.execute(create_table_query)

            create_idx_query = SQL("""
                CREATE INDEX IF NOT EXISTS {idx_name} 
                ON {table} USING hnsw (embedding vector_cosine_ops)
            """).format(
                idx_name=Identifier(f"{self.table_name}_embedding_idx"),
                table=Identifier(self.table_name),
            )
            conn.execute(create_idx_query)

    async def upsert(self, chunks: List[DocumentChunk], embeddings: List[List[float]]):
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks and embeddings must match!")

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                data = [
                    (chunk.id, chunk.text, json.dumps(chunk.metadata), embedding)
                    for chunk, embedding in zip(chunks, embeddings)
                ]

                upsert_query = SQL("""
                    INSERT INTO {table} (id, text, metadata, embedding)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE 
                    SET text = EXCLUDED.text, 
                        metadata = EXCLUDED.metadata, 
                        embedding = EXCLUDED.embedding
                """).format(table=Identifier(self.table_name))

                cur.executemany(upsert_query, data)

    async def search(
        self,
        query_vector: List[float],
        top_k: int,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[DocumentChunk]:
        if len(query_vector) != self.dimension:
            raise ValueError(
                f"Query vector size {len(query_vector)} does not match DB dimension {self.dimension}"
            )

        # 1. Base query selection (Placeholder 1: %s for calculating score)
        base_query: List[Union[SQL, Composed]] = [
            SQL(
                "SELECT id, text, metadata, 1 - (embedding <=> %s::vector) AS score FROM {table}"
            ).format(table=Identifier(self.table_name))
        ]
        params: List[Any] = [query_vector]

        # 2. Conditional filter (Placeholder 2 if truthy: %s for metadata string matching)
        if filters and "source" in filters:
            source_file = filters["source"].get("$eq")
            if source_file:
                base_query.append(SQL("WHERE metadata->>'source' = %s"))
                params.append(source_file)

        # 3. Dynamic ordering block (Placeholders 3 & 4: %s for HNSW evaluation, %s for limit integer)
        base_query.append(SQL("ORDER BY embedding <=> %s::vector LIMIT %s"))
        params.extend([query_vector, top_k])

        # FIX: Join exactly once, and execute safely. No duplicate parameter extensions.
        final_query = SQL(" ").join(base_query)
        results = []

        with self._get_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(final_query, params)
                rows = cur.fetchall()

                for row in rows:
                    results.append(
                        DocumentChunk(
                            id=str(row["id"]),
                            text=str(row["text"]),
                            metadata=row["metadata"],
                            score=float(row["score"]),
                        )
                    )
        return results
