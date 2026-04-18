from pydantic import BaseModel


class FrontendConfig(BaseModel):
    APP_HOST: str
    APP_PORT: int
    DEBUG: bool
    USE_LOCAL_DB: bool
    LOCAL_MODEL: str
    LLM_MODEL: str
    LLM_TEMP: float
    EMBEDDING_MODEL: str
    EMBEDDING_DIMENSION: int
    EMBEDDING_MODEL_MAX_TOKEN: int
    SYSTEM_PROMPT_FILE: str
    CHUNKING_STRATEGY: str
    ENABLE_TABLE_PARSING: bool
    TOP_K: int
    INDEX_NAME: str
    CLOUD: str
    REGION: str
    BATCH_SIZE: int
