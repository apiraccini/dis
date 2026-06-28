"""In-memory DocumentRepository implementation.

Canonical test double: proves the Protocol contract without a live database.
Also usable as the repository backing service-layer / MCP tests in later tasks.
"""

from __future__ import annotations

import copy
import uuid
from uuid import UUID

from src.core.errors import DocumentNotFoundError, DuplicateDocumentError
from src.models.document import Document, DocumentStatus, normalize_tags

__all__ = ['InMemoryDocumentRepository']


class InMemoryDocumentRepository:
    """Dict-backed async document store."""

    def __init__(self) -> None:
        self._store: dict[UUID, Document] = {}

    async def create(self, document: Document) -> Document:
        # Normalize tags before persisting.
        document.tags = normalize_tags(document.tags)
        if document.id is None:
            document.id = uuid.uuid4()
        if any(d.content_hash == document.content_hash for d in self._store.values()):
            raise DuplicateDocumentError(
                f'document with content_hash {document.content_hash!r} already exists'
            )
        self._store[document.id] = document
        return copy.deepcopy(document)

    async def get_by_id(self, document_id: UUID) -> Document | None:
        doc = self._store.get(document_id)
        return copy.deepcopy(doc) if doc is not None else None

    async def get_by_hash(self, content_hash: str) -> Document | None:
        for doc in self._store.values():
            if doc.content_hash == content_hash:
                return copy.deepcopy(doc)
        return None

    async def list_documents(
        self,
        offset: int = 0,
        limit: int = 100,
        tag: str | None = None,
    ) -> tuple[list[Document], int]:
        tag_norm = tag.strip().lower() if tag else None
        matching = [doc for doc in self._store.values() if tag_norm is None or tag_norm in doc.tags]
        total = len(matching)
        page = matching[offset : offset + limit]
        return [copy.deepcopy(d) for d in page], total

    async def update_status(
        self,
        document_id: UUID,
        status: DocumentStatus,
        error_message: str | None = None,
    ) -> Document:
        doc = self._store.get(document_id)
        if doc is None:
            raise DocumentNotFoundError(f'no document with id {document_id}')
        doc.status = status
        doc.error_message = error_message
        return copy.deepcopy(doc)

    async def update_chunk_count(
        self,
        document_id: UUID,
        chunk_count: int,
    ) -> Document:
        doc = self._store.get(document_id)
        if doc is None:
            raise DocumentNotFoundError(f'no document with id {document_id}')
        doc.chunk_count = chunk_count
        return copy.deepcopy(doc)

    async def delete(self, document_id: UUID) -> None:
        if document_id not in self._store:
            raise DocumentNotFoundError(f'no document with id {document_id}')
        del self._store[document_id]
