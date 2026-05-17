from fastapi import APIRouter

from app.core.config import settings
from app.models.frontend_config import FrontendConfig

router = APIRouter()


@router.get("", response_model=FrontendConfig, summary="Get frontend configuration")
async def get_frontend_config():
    """
    Exposes non-sensitive backend configuration for frontend clients.
    Allows UI adjustments based on current model types and context windows.
    """
    return FrontendConfig(
        # ==========================================
        # 1. Core Application Metadata
        # ==========================================
        APP_HOST=settings.APP_HOST,
        APP_PORT=settings.APP_PORT,
        DEBUG=settings.DEBUG,
        USE_LOCAL_DB=settings.USE_LOCAL_DB,
        # ==========================================
        # 2. Dynamic Model Providers & Engines
        # ==========================================
        LLM_PROVIDER=settings.LLM_PROVIDER,
        LOCAL_MODEL=settings.LOCAL_MODEL,
        AVAILABLE_LOCAL_MODELS=settings.AVAILABLE_LOCAL_MODELS,
        LLM_MODEL=settings.LLM_MODEL,
        OLLAMA_MODEL=settings.OLLAMA_MODEL,
        REMOTE_LLAMACPP_URL=settings.REMOTE_LLAMACPP_URL,
        OLLAMA_BASE_URL=settings.OLLAMA_BASE_URL,
        # ==========================================
        # 3. Guardrails & Token Constraints
        # ==========================================
        LLM_TEMP=settings.LLM_TEMP,
        LLM_MAX_TOKENS=settings.LLM_MAX_TOKENS,
        LLM_N_CTX=settings.LLM_N_CTX,
        LLM_STOP_SEQUENCES=settings.LLM_STOP_SEQUENCES,
        # ==========================================
        # 4. Embeddings & Vector Space Data
        # ==========================================
        EMBEDDING_MODEL=settings.EMBEDDING_MODEL,
        EMBEDDING_DIMENSION=settings.EMBEDDING_DIMENSION,
        EMBEDDING_MODEL_MAX_TOKEN=settings.EMBEDDING_MODEL_MAX_TOKEN,
        # ==========================================
        # 5. Pipeline RAG Orchestration
        # ==========================================
        SYSTEM_PROMPT_FILE=settings.SYSTEM_PROMPT_FILE,
        CHUNKING_STRATEGY=settings.CHUNKING_STRATEGY,
        ENABLE_TABLE_PARSING=settings.ENABLE_TABLE_PARSING,
        TOP_K=settings.TOP_K,
        # ==========================================
        # 6. Database / Infrastructure Ecosystem
        # ==========================================
        INDEX_NAME=settings.PINECONE_INDEX_NAME,
        CLOUD=settings.CLOUD,
        REGION=settings.REGION,
        BATCH_SIZE=settings.BATCH_SIZE,
    )
