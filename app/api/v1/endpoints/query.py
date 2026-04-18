from fastapi import APIRouter, Depends
from app.models.api_requests import ChatRequest
from app.models.api_response import QueryResponse
from app.core.dependencies import get_rag_engine, load_prompt

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
    if request.prompt_name:
        engine.system_prompt = load_prompt(request.prompt_name)

    result = await engine.answer_question(
        query=request.message,
        file_filter=request.file_name,
        translation_strategy=request.translation_strategy,
    )
    return result
