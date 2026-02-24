import uvicorn
from fastapi import FastAPI

from app.api.routes import router
from app.core.config import settings

# Initialize FastAPI
app = FastAPI(
    title="RAG Framework API", description="Modular RAG engine", version="1.0.0"
)

# Include the routes we defined above
app.include_router(router, prefix="/api/v1")


# Root endpoint for health check
@app.get("/")
def health_check():
    return {
        "status": "healthy",
        "mode": settings.CLOUD,
        "vector_db": settings.INDEX_NAME,
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
    )
