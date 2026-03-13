import uvicorn
from fastapi import FastAPI
from datetime import datetime

from app.api.routes import router
from app.core.config import settings

# Initialize FastAPI
app = FastAPI(
    title="RAG Framework API",
    description="Modular RAG engine",
    version="1.0.0",
    debug=settings.DEBUG,
)

# Include the routes we defined above
app.include_router(router, prefix="/api/v1")


# Root endpoint for health check
@app.get("/")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "app": {
            "host": settings.APP_HOST,
            "port": settings.APP_PORT,
            "workers": settings.APP_WORKERS,
            "debug": settings.DEBUG,
        },
        "database": {
            "using_local_db": settings.USE_LOCAL_DB,
            "db_url": settings.DATABASE_URL,
        },
        "models": {
            "llm_model": settings.LLM_MODEL,
            "embedding_model": settings.EMBEDDING_MODEL,
            "embedding_dimension": settings.EMBEDDING_DIMENSION,
            "local_model": settings.LOCAL_MODEL if settings.USE_LOCAL_DB else None,
        },
        "rag_settings": {
            "chunking_strategy": settings.CHUNKING_STRATEGY,
            "batch_size": settings.BATCH_SIZE,
            "top_k": settings.TOP_K,
            "table_parsing_enabled": settings.ENABLE_TABLE_PARSING,
        },
        "vector_db": {
            "provider": "pgvector" if settings.USE_LOCAL_DB else "pinecone",
            "index_name": settings.INDEX_NAME if not settings.USE_LOCAL_DB else None,
            "cloud": settings.CLOUD if not settings.USE_LOCAL_DB else None,
            "region": settings.REGION if not settings.USE_LOCAL_DB else None,
        },
    }


if __name__ == "__main__":
    # Run the server
    # Host 0.0.0.0 makes it accessible on your local network
    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.APP_RELOAD,
        workers=settings.APP_WORKERS,
        log_level="debug",
    )
