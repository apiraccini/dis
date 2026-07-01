from __future__ import annotations

from src.repositories.protocols import SparseVector
from src.services.protocols import Embedder, SparseEmbedder

__all__ = ['FailingEmbedder', 'FailingSparseEmbedder']


class FailingEmbedder:
    def __init__(self, dimension: int = 4, exc: Exception | None = None) -> None:
        self._dimension = dimension
        self._exc = exc or RuntimeError('embedder exploded')

    @property
    def dimension(self) -> int:
        return self._dimension

    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise self._exc


class FailingSparseEmbedder:
    def __init__(self, exc: Exception | None = None) -> None:
        self._exc = exc or RuntimeError('sparse embedder exploded')

    async def embed(self, texts: list[str]) -> list[SparseVector]:
        raise self._exc


assert isinstance(FailingEmbedder(), Embedder)
assert isinstance(FailingSparseEmbedder(), SparseEmbedder)
