from fastapi import APIRouter, Depends

from app.components.query_translation.enricher import enrich_query
from app.core.dependencies import get_rag_engine, load_prompt
from app.models.api_requests import ChatRequest
from app.models.api_response import QueryResponse

router = APIRouter()


@router.post("", response_model=QueryResponse, summary="Query the RAG knowledge base")
async def query_knowledge_base(request: ChatRequest, engine=Depends(get_rag_engine)):
    """
    Search and Answer based on ingested knowledge.

    - **message**: Your question
    - **file_name**: Optional filter to a specific file
    - **translation_strategy**: Optional strategy (multi_query, hyde, etc.)
    - **prompt_name**: Optional custom system prompt name
    """
    system_prompt = load_prompt(request.prompt_name) if request.prompt_name else None
    enriched_query = enrich_query(request.message, request.file_name)

    result = await engine.answer_question(
        query=enriched_query,
        file_filter=request.file_name,
        translation_strategy=request.translation_strategy,
        system_prompt=system_prompt,
    )
    return result
