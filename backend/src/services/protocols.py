from typing import Protocol, runtime_checkable


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


__all__ = ['Chunker', 'Embedder', 'Parser']
