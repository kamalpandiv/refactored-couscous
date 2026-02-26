import psycopg

from app.core.config import settings


def reset_vector_table():
    print(f"Connecting to {settings.DATABASE_URL}...")

    # Connect to DB
    with psycopg.connect(settings.DATABASE_URL, autocommit=True) as conn:
        # 1. Drop the specific table for the current dimension
        # If you implemented the dynamic naming:
        table_name = f"rag_vectors_{settings.EMBEDDING_DIMENSION}"

        # OR if you are using the default name:
        # table_name = "rag_vectors"

        print(f"Dropping table: {table_name}")
        conn.execute(f"DROP TABLE IF EXISTS {table_name}")

        print("Table dropped. Restart your app to recreate it with new dimensions.")


if __name__ == "__main__":
    reset_vector_table()
