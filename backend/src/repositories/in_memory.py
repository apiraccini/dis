from __future__ import annotations

import copy
import math
import uuid
from uuid import UUID

from src.core.errors import DocumentNotFoundError, DuplicateDocumentError
from src.models.document import Document, DocumentStatus, normalize_tags
from src.repositories.protocols import ChunkRecord, SearchHit

__all__ = ['InMemoryDocumentRepository', 'InMemoryVectorStore']


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

    async def list_by_status(
        self,
        status: DocumentStatus,
        offset: int = 0,
        limit: int = 1000,
    ) -> tuple[list[Document], int]:
        matching = [doc for doc in self._store.values() if doc.status == status]
        total = len(matching)
        page = matching[offset : offset + limit]
        return [copy.deepcopy(d) for d in page], total


class InMemoryVectorStore:
    """Dict-backed async vector store (canonical test double).

    Cosine similarity over stored vectors; tag/document_id filters applied
    in-memory to mirror the filter pushdown a Qdrant implementation will do.
    """

    def __init__(self) -> None:
        self._vectors: dict[UUID, list[tuple[ChunkRecord, list[float]]]] = {}

    async def upsert(
        self,
        document_id: UUID,
        chunks: list[ChunkRecord],
        vectors: list[list[float]],
    ) -> None:
        if len(chunks) != len(vectors):
            raise ValueError('chunks and vectors must have equal length')
        # Atomic replace: re-ingestion overwrites prior chunks for the document.
        self._vectors[document_id] = [
            (copy.deepcopy(c), list(v)) for c, v in zip(chunks, vectors, strict=True)
        ]

    async def delete_by_document(self, document_id: UUID) -> None:
        self._vectors.pop(document_id, None)

    async def provision(self, dim: int) -> None:
        pass  # In-memory store doesn't need provisioning

    async def search(
        self,
        query: list[float],
        top_k: int,
        *,
        tags: list[str] | None = None,
        document_ids: list[UUID] | None = None,
    ) -> list[SearchHit]:
        tags_norm = {t.strip().lower() for t in tags} if tags else None
        ids_norm = set(document_ids) if document_ids else None

        scored: list[SearchHit] = []
        for doc_id, entries in self._vectors.items():
            if ids_norm is not None and doc_id not in ids_norm:
                continue
            for chunk, vec in entries:
                if tags_norm is not None and not (
                    tags_norm & {t.strip().lower() for t in chunk.tags}
                ):
                    continue
                score = _cosine(query, vec)
                scored.append(
                    SearchHit(
                        document_id=doc_id,
                        document_name=chunk.document_name,
                        tags=list(chunk.tags),
                        chunk_index=chunk.chunk_index,
                        text=chunk.text,
                        score=score,
                    )
                )
        scored.sort(key=lambda h: h.score, reverse=True)
        return scored[:top_k]


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)
