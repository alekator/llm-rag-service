from __future__ import annotations

from openai import AsyncOpenAI

from app.core.settings import get_settings


class EmbeddingsClient:
    def __init__(self) -> None:
        s = get_settings()

        api_key = getattr(s, "openai_api_key", None)
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")

        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=getattr(s, "openai_base_url", None),
        )

        self._model: str = getattr(
            s,
            "openai_embeddings_model",
            "text-embedding-3-small",
        )

    async def embed(self, texts: list[str]) -> list[list[float]]:
        resp = await self._client.embeddings.create(
            model=self._model,
            input=texts,
        )
        return [d.embedding for d in resp.data]
