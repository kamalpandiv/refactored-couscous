import json
from typing import Dict, List

import psycopg
from pgvector.psycopg import register_vector
from psycopg.rows import dict_row

from app.core.config import settings
from app.core.interfaces import BaseVectorDB
from app.models.domain import DocumentChunk


class PGVectorDB(BaseVectorDB):
    def __init__(self):
        # 1. Use Settings, not hardcoded string
        self.db_url = settings.DATABASE_URL

        # 2. Get dimension from config (e.g., 1536 or 512)
        self.dimension = settings.EMBEDDING_DIMENSION

        # 3. Dynamic Table Name
        self.table_name = f"rag_vectors_{self.dimension}"
        print(f"rag_vectors_{self.dimension}")

        # Initialize DB
        self._init_db()

    def _get_connection(self):
        conn = psycopg.connect(self.db_url, row_factory=dict_row, autocommit=True)
        # 4. Wrap register_vector in try/except
        # If the extension doesn't exist yet (first run), this fails.
        # We catch it so _init_db can proceed to create it.
        try:
            register_vector(conn)
        except psycopg.ProgrammingError:
            pass
        return conn

    def _init_db(self):
        """Creates the vector extension and the table."""
        # Use a raw connection here to avoid dependency loops
        with psycopg.connect(self.db_url, autocommit=True) as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS vector")

            # Now safe to register
            register_vector(conn)

            # 5. Use {self.dimension}, not 1536
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    id TEXT PRIMARY KEY,
                    text TEXT,
                    metadata JSONB,
                    embedding vector({self.dimension})
                )
            """)

            # Create Index
            conn.execute(f"""
                CREATE INDEX IF NOT EXISTS {self.table_name}_embedding_idx 
                ON {self.table_name} USING hnsw (embedding vector_cosine_ops)
            """)

    async def upsert(self, chunks: List[DocumentChunk], embeddings: List[List[float]]):

        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks and embeddings must match!")

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                data = [
                    # Use 'embedding' from the loop, not 'chunk.vector'
                    (chunk.id, chunk.text, json.dumps(chunk.metadata), embedding)
                    for chunk, embedding in zip(chunks, embeddings)
                ]

                cur.executemany(
                    f"""
                    INSERT INTO {self.table_name} (id, text, metadata, embedding)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE 
                    SET text = EXCLUDED.text, 
                        metadata = EXCLUDED.metadata, 
                        embedding = EXCLUDED.embedding
                    """,
                    data,
                )

    async def search(
        self, query_vector: List[float], top_k: int, filters: Dict = None
    ) -> List[DocumentChunk]:
        # 6. Validation: Check if query matches DB dimension
        if len(query_vector) != self.dimension:
            raise ValueError(
                f"Query vector size {len(query_vector)} does not match DB dimension {self.dimension}"
            )

        # 7. Explicit Casting: ::vector(N)
        query_sql = f"""
            SELECT id, text, metadata, 
                   1 - (embedding <=> %s::vector({self.dimension})) AS score 
            FROM {self.table_name}
        """
        params = [query_vector]

        if filters and "source" in filters:
            source_file = filters["source"].get("$eq")
            if source_file:
                query_sql += " WHERE metadata->>'source' = %s"
                params.append(source_file)

        query_sql += f" ORDER BY embedding <=> %s::vector({self.dimension}) LIMIT %s"
        params.append(query_vector)
        params.append(top_k)

        results = []
        with self._get_connection() as conn:
            rows = conn.execute(query_sql, params).fetchall()

            for row in rows:
                results.append(
                    DocumentChunk(
                        id=row["id"],
                        text=row["text"],
                        metadata=row["metadata"],
                        score=row["score"],
                    )
                )
        return results
