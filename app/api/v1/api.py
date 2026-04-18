from fastapi import APIRouter
from app.api.v1.endpoints import ingest, query, config

api_router = APIRouter()

api_router.include_router(ingest.router, prefix="/ingest", tags=["Ingestion"])
api_router.include_router(query.router, prefix="/query", tags=["Retrieval"])
api_router.include_router(config.router, prefix="/config", tags=["Configuration"])
