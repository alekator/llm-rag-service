from __future__ import annotations

from app.core.settings import get_settings


async def generate_answer_llm(*, question: str, context: str) -> str:
    """
    LLM intentionally optional.
    If no key — fail fast and be handled by caller.
    """
    settings = get_settings()

    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    # Реальную реализацию позже
    return "LLM disabled (stub)"
