from __future__ import annotations

import hashlib
import math
from typing import Final

from openai import AsyncOpenAI

from app.core.settings import get_settings


def _l2_normalize(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in vec))
    if norm == 0.0:
        return vec
    return [x / norm for x in vec]


def _mock_embedding(text: str, dim: int) -> list[float]:
    """
    Deterministic embedding based on sha256(text + counter).
    Same input => same vector. Good for local/dev without OpenAI.
    """
    out: list[float] = []
    counter = 0
    # generate enough bytes to fill dim floats
    while len(out) < dim:
        h = hashlib.sha256(f"{counter}:{text}".encode()).digest()
        # digest is 32 bytes -> 8 x uint32
        for i in range(0, len(h), 4):
            if len(out) >= dim:
                break
            u = int.from_bytes(h[i : i + 4], "little", signed=False)
            # map to [-1, 1]
            out.append((u / 2**32) * 2.0 - 1.0)
        counter += 1

    return _l2_normalize(out)


class EmbeddingsClient:
    _DEFAULT_OPENAI_MODEL: Final[str] = "text-embedding-3-small"

    def __init__(self) -> None:
        s = get_settings()

        backend = s.embeddings_backend.lower().strip()
        if backend not in {"auto", "openai", "mock"}:
            raise RuntimeError(f"Invalid APP_EMBEDDINGS_BACKEND={s.embeddings_backend!r}")

        self._dim: int = s.embeddings_dim
        self._use_openai: bool

        api_key = s.openai_api_key
        if backend == "openai":
            if not api_key:
                raise RuntimeError("OPENAI_API_KEY is not set but embeddings_backend=openai")
            self._use_openai = True
        elif backend == "mock":
            self._use_openai = False
        else:
            # auto
            self._use_openai = bool(api_key)

        self._client: AsyncOpenAI | None = None
        self._model: str = s.openai_embeddings_model or self._DEFAULT_OPENAI_MODEL

        if self._use_openai:
            # base_url может быть None — это ок
            self._client = AsyncOpenAI(api_key=api_key, base_url=s.openai_base_url)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        if not self._use_openai:
            return [_mock_embedding(t, self._dim) for t in texts]

        # openai path
        assert self._client is not None
        resp = await self._client.embeddings.create(model=self._model, input=texts)
        return [d.embedding for d in resp.data]
