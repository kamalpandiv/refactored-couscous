from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile
from app.components.loaders.pdf_loader import parse_pdf
from app.models.api_requests import IngestRequest, UrlIngestRequest
from app.components.loaders.web_loader import parse_url
from app.core.dependencies import get_ingestion_service
from app.models.api_response import IngestResponse

router = APIRouter()


@router.post("/file", response_model=IngestResponse, summary="Ingest a PDF or TXT file")
async def ingest_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    service=Depends(get_ingestion_service),
):
    """
    Upload a PDF or TXT file to ingest.
    The processing happens asynchronously in the background.
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

    return IngestResponse(
        filename=file.filename,
        status="Ingestion started in background",
    )


@router.post("/url", response_model=IngestResponse, summary="Ingest content from a URL")
async def ingest_url(
    background_tasks: BackgroundTasks,
    request: UrlIngestRequest,
    service=Depends(get_ingestion_service),
):
    """
    Scrape a website and ingest the text.
    The processing happens asynchronously in the background.
    """
    text = parse_url(request.url)

    if not text:
        return {"error": "Could not extract text from URL"}

    background_tasks.add_task(
        service.ingest_texts,
        texts=[text],
        source_name=request.url,
    )

    return IngestResponse(url=request.url, status="Ingestion started in background")


@router.post(
    "/custom", response_model=IngestResponse, summary="Ingest custom text strings"
)
async def ingest_custom_text(
    request: IngestRequest, service=Depends(get_ingestion_service)
):
    """Ingest any list of strings directly as JSON."""
    await service.ingest_texts(request.texts, source_name="manual_upload")
    return IngestResponse(status="success", count=len(request.texts))
