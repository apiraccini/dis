from typing import Protocol, runtime_checkable

from src.repositories.protocols import SparseVector


@runtime_checkable
class Parser(Protocol):
    async def parse(self, content: bytes, filename: str) -> str: ...


@runtime_checkable
class Chunker(Protocol):
    def chunk(self, text: str) -> list[str]: ...


@runtime_checkable
class Embedder(Protocol):
    @property
    def dimension(self) -> int: ...

    async def embed(self, texts: list[str]) -> list[list[float]]: ...


@runtime_checkable
class SparseEmbedder(Protocol):
    async def embed(self, texts: list[str]) -> list[SparseVector]: ...


__all__ = ['Chunker', 'Embedder', 'Parser', 'SparseEmbedder']
