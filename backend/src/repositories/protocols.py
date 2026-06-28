"""Repository Protocols (interfaces) for data access.

Each Protocol is async and implementation-agnostic. Two implementations back
each protocol: a SQLModel impl (production) and an in-memory impl (canonical
test double). Both raise the domain exceptions from `src.core.errors`.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable
from uuid import UUID

from src.core.errors import DocumentNotFoundError, DuplicateDocumentError  # noqa: F401
from src.models.document import Document, DocumentStatus

__all__ = ['DocumentRepository']


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
