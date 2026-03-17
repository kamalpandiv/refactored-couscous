from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile
from pydantic import BaseModel

from app.components.loaders.pdf_loader import parse_pdf
from app.components.loaders.web_loader import parse_url
from app.components.query_translation import QueryTranslationStrategyType
from app.core.dependencies import get_ingestion_service, get_rag_engine, load_prompt

router = APIRouter()


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
    prompt_name: Optional[str] = None 


# --- Endpoints ---


@router.post("/query")
async def query_knowledge_base(request: ChatRequest, engine=Depends(get_rag_engine)):
    """
    Search and Answer.
    If 'file_name' is provided, it only searches inside that specific file.
    If 'translation_strategy' is provided, it applies that strategy.
    """
    if request.prompt_name:
        engine.system_prompt = load_prompt(request.prompt_name)
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
    service=Depends(get_ingestion_service),
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
    service=Depends(get_ingestion_service),
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


@router.post("/ingest/custom")
async def ingest_custom_text(
    request: IngestRequest, service=Depends(get_ingestion_service)
):
    """Ingest any list of strings you send as JSON."""
    await service.ingest_texts(request.texts, source_name="manual_upload")
    return {"status": "success", "count": len(request.texts)}
