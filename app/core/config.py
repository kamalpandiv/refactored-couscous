from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env early (optional but safe)
load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # =========================
    # App Settings
    # =========================
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    APP_WORKERS: int = 1
    APP_RELOAD: bool = True
    DEBUG: bool = True
    USE_LOCAL_DB: bool = True

    # =========================
    # API Keys
    # =========================
    OPENAI_API_KEY: str = ""
    PINECONE_API_KEY: str = ""

    # =========================
    # Database
    # =========================
    DATABASE_URL: str = "postgresql://postgres:123456@localhost:5432/rag_db"

    # =========================
    # LLM Settings
    # =========================
    LOCAL_MODEL: str = "models/Hermes-2-Pro-Llama-3-8B.Q4_K_M.gguf"
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_TEMP: float = 0.3

    # =========================
    # Embeddings
    # =========================
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSION: int = 512
    EMBEDDING_MODEL_MAX_TOKEN: int = 8000

    # =========================
    # Retrieval / RAG
    # =========================
    SYSTEM_PROMPT_FILE: str = "can_spam"
    CHUNKING_STRATEGY: str = "recursive"
    ENABLE_TABLE_PARSING: bool = True
    TOP_K: int = 10

    # =========================
    # Pinecone
    # =========================
    INDEX_NAME: str = "semantic-search-openai"
    CLOUD: str = "aws"
    REGION: str = "us-east-1"

    # =========================
    # Processing
    # =========================
    BATCH_SIZE: int = 32


settings = Settings()
