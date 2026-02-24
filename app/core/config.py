import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# 1. Force load the .env file immediately
load_dotenv()


class Settings(BaseSettings):
    APP_HOST: str = os.getenv("APP_HOST", "")
    APP_PORT: int = int(os.getenv("APP_PORT", ""))
    APP_WORKERS: int = int(os.getenv("APP_WORKERS", ""))
    APP_RELOAD: bool = False
    USE_LOCAL_DB: bool = True

    # API Keys
    # We use os.getenv to fetch the values loaded above
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    DATABASE_URL: str = "postgresql://postgres:123456@localhost:5432/rag_db"

    # Model Settings
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    LOCAL_MODEL: str = "models/Hermes-2-Pro-Llama-3-8B.Q4_K_M.gguf"
    EMBEDDING_MODEL_MAX_TOKEN: int = 8000
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_TEMP: float = 0.3

    # NEW: Central source of truth for vector size
    # Options: 1536 (default), 512 (faster), 1024, 3072 (large model)
    EMBEDDING_DIMENSION: int = 512
    ENABLE_TABLE_PARSING: bool = True
    CHUNKING_STRATEGY: str = "recursive"  # use recursive or semantic

    # Pinecone Settings
    INDEX_NAME: str = "semantic-search-openai"
    CLOUD: str = "aws"
    REGION: str = "us-east-1"

    # Processing Settings
    BATCH_SIZE: int = 32
    TOP_K: int = 8

    # Tells Pydantic to read from .env if it can't find keys
    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
