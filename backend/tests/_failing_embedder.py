from __future__ import annotations

from src.services.protocols import Embedder

__all__ = ['FailingEmbedder']


class FailingEmbedder:
    def __init__(self, dimension: int = 4, exc: Exception | None = None) -> None:
        self._dimension = dimension
        self._exc = exc or RuntimeError('embedder exploded')

    @property
    def dimension(self) -> int:
        return self._dimension

    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise self._exc


assert isinstance(FailingEmbedder(), Embedder)
