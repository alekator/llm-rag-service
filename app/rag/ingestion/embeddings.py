from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Literal, Protocol

from openai import AsyncOpenAI

from app.core.settings import get_settings


class EmbeddingsBackend(Protocol):
    @property
    def dim(self) -> int: ...
    async def embed(self, texts: list[str]) -> list[list[float]]: ...


@dataclass(frozen=True)
class OpenAIEmbeddingsBackend:
    client: AsyncOpenAI
    model: str
    _dim: int

    @property
    def dim(self) -> int:
        return self._dim

    async def embed(self, texts: list[str]) -> list[list[float]]:
        resp = await self.client.embeddings.create(model=self.model, input=texts)
        return [d.embedding for d in resp.data]


@dataclass(frozen=True)
class MockEmbeddingsBackend:
    _dim: int = 1536

    @property
    def dim(self) -> int:
        return self._dim

    async def embed(self, texts: list[str]) -> list[list[float]]:
        # детерминированные эмбеддинги: одинаковый текст -> одинаковый вектор
        out: list[list[float]] = []
        for t in texts:
            h = hashlib.sha256(t.encode("utf-8")).digest()
            # растягиваем hash до нужной длины
            raw = (h * ((self._dim // len(h)) + 1))[: self._dim]
            vec = [(b - 128) / 128.0 for b in raw]  # [-1..1]
            out.append(vec)
        return out


class EmbeddingsClient:
    def __init__(self) -> None:
        s = get_settings()

        backend: Literal["auto", "openai", "mock"] = getattr(s, "embeddings_backend", "auto")
        dim: int = getattr(s, "embeddings_dim", 1536)

        if backend == "auto":
            backend = "openai" if getattr(s, "openai_api_key", None) else "mock"

        if backend == "openai":
            api_key = getattr(s, "openai_api_key", None)
            if not api_key:
                raise RuntimeError("OPENAI_API_KEY is not set")

            client = AsyncOpenAI(api_key=api_key, base_url=getattr(s, "openai_base_url", None))
            model = getattr(s, "openai_embeddings_model", "text-embedding-3-small")
            self._backend: EmbeddingsBackend = OpenAIEmbeddingsBackend(
                client=client,
                model=model,
                _dim=dim,
            )
        else:
            self._backend = MockEmbeddingsBackend(_dim=dim)

    @property
    def dim(self) -> int:
        return self._backend.dim

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return await self._backend.embed(texts)
