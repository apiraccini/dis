from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable
from uuid import UUID

from src.core.config import settings
from src.core.errors import DocumentNotFoundError, DuplicateDocumentError  # noqa: F401
from src.models.document import Document, DocumentStatus

__all__ = [
    'ChunkPayload',
    'DocumentRepository',
    'SearchHit',
    'SparseVector',
    'VectorStore',
    'clamp_pagination',
]


def clamp_pagination(offset: int, limit: int) -> tuple[int, int]:
    """Clamp pagination args to safe bounds: offset >= 0, 0 <= limit <= settings.max_page_size."""
    return max(offset, 0), max(0, min(limit, settings.max_page_size))


@runtime_checkable
class DocumentRepository(Protocol):
    """Async document store.

    Contract:
    - `create` raises `DuplicateDocumentError` if `content_hash` already exists.
    - `update_*` / `delete` raise `DocumentNotFoundError` if the id is absent.
    - `get_*` return `None` (not an exception) when nothing matches.
    - `list_documents` returns `(rows, total)` where `total` is the count before pagination.
      `offset`/`limit` are clamped to safe bounds (see `clamp_pagination`).
    """

    async def create(self, document: Document) -> Document: ...

    async def get_by_id(self, document_id: UUID) -> Document | None: ...

    async def get_by_hash(self, content_hash: str) -> Document | None: ...

    async def list_documents(
        self,
        offset: int = 0,
        limit: int = 100,
        tag: str | None = None,
    ) -> tuple[list[Document], int]: ...

    async def update_status(
        self,
        document_id: UUID,
        status: DocumentStatus,
        error_message: str | None = None,
    ) -> Document: ...

    async def update_chunk_count(
        self,
        document_id: UUID,
        chunk_count: int,
    ) -> Document: ...

    async def delete(self, document_id: UUID) -> None: ...

    async def list_by_status(
        self,
        status: DocumentStatus,
        offset: int = 0,
        limit: int = 1000,
    ) -> tuple[list[Document], int]: ...

    async def list_all_tags(self) -> list[str]: ...


@dataclass(frozen=True)
class SparseVector:
    """A lexical (BM25) sparse vector: term indices paired with weights."""

    indices: list[int]
    values: list[float]


@dataclass(frozen=True)
class ChunkPayload:
    """Payload stored alongside each vector."""

    document_id: UUID
    document_name: str
    tags: list[str]
    chunk_index: int
    text: str


@dataclass(frozen=True)
class SearchHit:
    """A single search result: a chunk plus its similarity score."""

    document_id: UUID
    document_name: str
    tags: list[str]
    chunk_index: int
    text: str
    score: float


@runtime_checkable
class VectorStore(Protocol):
    """Async vector store over chunk embeddings.

    Contract:
    - `upsert` atomically replaces all chunks for a document.
    - `search` fuses dense and sparse retrieval (RRF) and returns at most
      `top_k` hits; `tags` (OR) and `document_ids` (membership) are pushed
      into the query.
    """

    async def upsert(
        self,
        document_id: UUID,
        chunks: list[ChunkPayload],
        vectors: list[list[float]],
        sparse_vectors: list[SparseVector],
    ) -> None: ...

    async def delete_by_document(self, document_id: UUID) -> None: ...

    async def search(
        self,
        query: list[float],
        sparse_query: SparseVector,
        top_k: int,
        *,
        tags: list[str] | None = None,
        document_ids: list[UUID] | None = None,
    ) -> list[SearchHit]: ...

    async def provision(self, dim: int) -> None: ...
