from fastapi import APIRouter
from app.core.config import settings
from app.models.frontend_config import FrontendConfig

router = APIRouter()


@router.get("", response_model=FrontendConfig, summary="Get frontend configuration")
async def get_frontend_config():
    """
    Exposes non-sensitive backend configuration for frontend clients.
    """
    return FrontendConfig(
        APP_HOST=settings.APP_HOST,
        APP_PORT=settings.APP_PORT,
        DEBUG=settings.DEBUG,
        USE_LOCAL_DB=settings.USE_LOCAL_DB,
        LOCAL_MODEL=settings.LOCAL_MODEL,
        LLM_MODEL=settings.LLM_MODEL,
        LLM_TEMP=settings.LLM_TEMP,
        EMBEDDING_MODEL=settings.EMBEDDING_MODEL,
        EMBEDDING_DIMENSION=settings.EMBEDDING_DIMENSION,
        EMBEDDING_MODEL_MAX_TOKEN=settings.EMBEDDING_MODEL_MAX_TOKEN,
        SYSTEM_PROMPT_FILE=settings.SYSTEM_PROMPT_FILE,
        CHUNKING_STRATEGY=settings.CHUNKING_STRATEGY,
        ENABLE_TABLE_PARSING=settings.ENABLE_TABLE_PARSING,
        TOP_K=settings.TOP_K,
        INDEX_NAME=settings.INDEX_NAME,
        CLOUD=settings.CLOUD,
        REGION=settings.REGION,
        BATCH_SIZE=settings.BATCH_SIZE,
    )
