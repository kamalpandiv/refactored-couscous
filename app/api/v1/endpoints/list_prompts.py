from fastapi import APIRouter

from app.core.prompt_loader import get_available_prompts

router = APIRouter()


@router.get("", summary="List all discoverable system and user prompts")
async def list_prompts():
    return {
        "system_prompts": get_available_prompts("system"),
        "user_prompts": get_available_prompts("user"),
    }
