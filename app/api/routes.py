from typing import List, Optional

from datasets import load_dataset
from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile
from pydantic import BaseModel

from app.components.embedders.openai_embedder import OpenAIEmbedder
from app.components.llms.openai_llm import OpenAILLM
from app.components.loaders.pdf_loader import parse_pdf
from app.components.loaders.web_loader import parse_url
from app.components.query_translation import QueryTranslationStrategyType
from app.components.vector_dbs.pgvector_db import PGVectorDB
from app.components.vector_dbs.pinecone_db import PineconeDB
from app.core.config import settings
from app.services.ingestion import IngestionService
from app.services.rag_engine import RAGEngine

router = APIRouter()

USE_LOCAL_DB: bool = settings.USE_LOCAL_DB


def get_db():
    if USE_LOCAL_DB:
        print("Using Local PGVector")
        return PGVectorDB()
    else:
        print("Using Pinecone")
        return PineconeDB()


# --- Dependency Injection ---
def get_ingestion_service() -> IngestionService:
    return IngestionService(embedder=OpenAIEmbedder(), vector_db=get_db())


def get_rag_engine() -> RAGEngine:
    # We initialize the engine with the necessary components
    return RAGEngine(vector_db=get_db(), embedder=OpenAIEmbedder(), llm=OpenAILLM())


# --- Data Models ---
class IngestRequest(BaseModel):
    texts: List[str]


class UrlIngestRequest(BaseModel):
    url: str


class ChatRequest(BaseModel):
    message: str
    file_name: Optional[str] = None
    # Allow users to specify the strategy (e.g., "multi_query", "hyde")
    translation_strategy: Optional[QueryTranslationStrategyType] = None


# --- Endpoints ---


@router.post("/query")
async def query_knowledge_base(
    request: ChatRequest, engine: RAGEngine = Depends(get_rag_engine)
):
    """
    Search and Answer.
    If 'file_name' is provided, it only searches inside that specific file.
    If 'translation_strategy' is provided, it applies that strategy.
    """
    result = await engine.answer_question(
        query=request.message,
        file_filter=request.file_name,
        translation_strategy=request.translation_strategy,
    )
    return result


@router.post("/ingest/file")
async def ingest_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    service: IngestionService = Depends(get_ingestion_service),
):
    """
    Upload a PDF or TXT file to ingest.
    """
    text = ""
    if file.filename.endswith(".pdf"):
        text = await parse_pdf(file)
    elif file.filename.endswith(".txt"):
        content = await file.read()
        text = content.decode("utf-8")
    else:
        return {"error": "Unsupported file type. Use .pdf or .txt"}

    background_tasks.add_task(
        service.ingest_texts,
        texts=[text],
        source_name=file.filename,
    )

    return {
        "filename": file.filename,
        "status": "Ingestion started in background",
    }


@router.post("/ingest/url")
async def ingest_url(
    background_tasks: BackgroundTasks,
    request: UrlIngestRequest,
    service: IngestionService = Depends(get_ingestion_service),
):
    """
    Scrape a website and ingest the text.
    """
    text = parse_url(request.url)

    if not text:
        return {"error": "Could not extract text from URL"}

    background_tasks.add_task(
        service.ingest_texts,
        texts=[text],
        source_name=request.url,
    )

    return {"url": request.url, "status": "Ingestion started in background"}


@router.post("/ingest/demo-data")
async def ingest_demo_data(
    background_tasks: BackgroundTasks,
    service: IngestionService = Depends(get_ingestion_service),
):
    """
    Triggers the AG News ingestion.
    """

    def _run_ingestion():
        print("Loading AG News dataset...")
        dataset = load_dataset("ag_news", split="train[:1000]")
        texts = dataset["text"]

        import asyncio

        asyncio.run(service.ingest_texts(texts, source_name="ag_news_demo"))

    background_tasks.add_task(_run_ingestion)
    return {
        "status": "Ingestion started in background",
        "dataset": "ag_news",
        "count": 1000,
    }


@router.post("/ingest/custom")
async def ingest_custom_text(
    request: IngestRequest, service: IngestionService = Depends(get_ingestion_service)
):
    """Ingest any list of strings you send as JSON."""
    await service.ingest_texts(request.texts, source_name="manual_upload")
    return {"status": "success", "count": len(request.texts)}
