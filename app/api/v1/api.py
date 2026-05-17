from fastapi import APIRouter

from app.api.v1.endpoints import config, ingest, list_prompts, query

api_router = APIRouter()

api_router.include_router(ingest.router, prefix="/ingest", tags=["Ingestion"])
api_router.include_router(query.router, prefix="/query", tags=["Retrieval"])
api_router.include_router(config.router, prefix="/config", tags=["Configuration"])
api_router.include_router(
    list_prompts.router,
    prefix="/prompts",
    tags=["List all System and user prompts from folder"],
)
