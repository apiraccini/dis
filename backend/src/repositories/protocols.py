from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable
from uuid import UUID

from src.core.errors import DocumentNotFoundError, DuplicateDocumentError  # noqa: F401
from src.models.document import Document, DocumentStatus

__all__ = [
    'ChunkRecord',
    'DocumentRepository',
    'SearchHit',
    'VectorStore',
]


@runtime_checkable
class DocumentRepository(Protocol):
    """Async document store.

    Contract:
    - `create` raises `DuplicateDocumentError` if `content_hash` already exists.
    - `update_*` / `delete` raise `DocumentNotFoundError` if the id is absent.
    - `get_*` return `None` (not an exception) when nothing matches.
    - `list_documents` returns `(rows, total)` where `total` is the count before pagination.
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


@dataclass(frozen=True)
class ChunkRecord:
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
    - `search` returns at most `top_k` hits ranked by descending similarity;
      `tags` (OR) and `document_ids` (membership) are pushed into the query.
    """

    async def upsert(
        self,
        document_id: UUID,
        chunks: list[ChunkRecord],
        vectors: list[list[float]],
    ) -> None: ...

    async def delete_by_document(self, document_id: UUID) -> None: ...

    async def search(
        self,
        query: list[float],
        top_k: int,
        *,
        tags: list[str] | None = None,
        document_ids: list[UUID] | None = None,
    ) -> list[SearchHit]: ...
