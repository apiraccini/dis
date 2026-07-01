from __future__ import annotations

import copy
import math
from datetime import UTC, datetime
from uuid import UUID

from src.core.errors import DocumentNotFoundError, DuplicateDocumentError
from src.models.document import Document, DocumentStatus, normalize_tags
from src.repositories.protocols import ChunkPayload, SearchHit, SparseVector, clamp_pagination

# RRF constant (k), matching Qdrant's default — dampens the impact of rank 1
# so a single method's top hit doesn't dominate the fused ranking.
_RRF_K = 60

__all__ = ['InMemoryDocumentRepository', 'InMemoryVectorStore']


class InMemoryDocumentRepository:
    """Dict-backed async document store."""

    def __init__(self) -> None:
        self._store: dict[UUID, Document] = {}

    async def create(self, document: Document) -> Document:
        # Normalize tags before persisting. `id` always has a uuid default on the model.
        document.tags = normalize_tags(document.tags)
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
        offset, limit = clamp_pagination(offset, limit)
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
        doc.updated_at = datetime.now(UTC)
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
        doc.updated_at = datetime.now(UTC)
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
        offset, limit = clamp_pagination(offset, limit)
        matching = [doc for doc in self._store.values() if doc.status == status]
        total = len(matching)
        page = matching[offset : offset + limit]
        return [copy.deepcopy(d) for d in page], total

    async def list_all_tags(self) -> list[str]:
        seen: set[str] = set()
        for doc in self._store.values():
            seen.update(doc.tags)
        return sorted(seen)


class InMemoryVectorStore:
    """Dict-backed async vector store (canonical test double).

    Approximates Qdrant's hybrid search: ranks candidates separately by dense
    cosine similarity and by sparse (lexical) dot-product overlap, then fuses
    both rankings via Reciprocal Rank Fusion (RRF). Tag/document_id filters
    are applied in-memory to mirror the filter pushdown a Qdrant
    implementation will do.
    """

    def __init__(self) -> None:
        self._vectors: dict[UUID, list[tuple[ChunkPayload, list[float], SparseVector]]] = {}

    async def upsert(
        self,
        document_id: UUID,
        chunks: list[ChunkPayload],
        vectors: list[list[float]],
        sparse_vectors: list[SparseVector],
    ) -> None:
        if not (len(chunks) == len(vectors) == len(sparse_vectors)):
            raise ValueError('chunks, vectors, and sparse_vectors must have equal length')
        # Atomic replace: re-ingestion overwrites prior chunks for the document.
        self._vectors[document_id] = [
            (copy.deepcopy(c), list(v), s)
            for c, v, s in zip(chunks, vectors, sparse_vectors, strict=True)
        ]

    async def delete_by_document(self, document_id: UUID) -> None:
        self._vectors.pop(document_id, None)

    async def provision(self, dim: int) -> None:
        pass  # In-memory store doesn't need provisioning

    async def search(
        self,
        query: list[float],
        sparse_query: SparseVector,
        top_k: int,
        *,
        tags: list[str] | None = None,
        document_ids: list[UUID] | None = None,
    ) -> list[SearchHit]:
        tags_norm = {t.strip().lower() for t in tags} if tags else None
        ids_norm = set(document_ids) if document_ids else None

        candidates: list[tuple[UUID, ChunkPayload, float, float]] = []
        for doc_id, entries in self._vectors.items():
            if ids_norm is not None and doc_id not in ids_norm:
                continue
            for chunk, vec, sparse in entries:
                if tags_norm is not None and not (
                    tags_norm & {t.strip().lower() for t in chunk.tags}
                ):
                    continue
                dense_score = _cosine(query, vec)
                sparse_score = _sparse_dot(sparse_query, sparse)
                candidates.append((doc_id, chunk, dense_score, sparse_score))

        dense_rank = _ranks(candidates, key=lambda c: c[2])
        sparse_rank = _ranks(candidates, key=lambda c: c[3])

        def rrf_score(i: int) -> float:
            return 1 / (_RRF_K + dense_rank[i]) + 1 / (_RRF_K + sparse_rank[i])

        ranked = sorted(range(len(candidates)), key=rrf_score, reverse=True)
        hits = [
            SearchHit(
                document_id=candidates[i][0],
                document_name=candidates[i][1].document_name,
                tags=list(candidates[i][1].tags),
                chunk_index=candidates[i][1].chunk_index,
                text=candidates[i][1].text,
                score=rrf_score(i),
            )
            for i in ranked
        ]
        return hits[:top_k]


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _sparse_dot(a: SparseVector, b: SparseVector) -> float:
    b_map = dict(zip(b.indices, b.values, strict=True))
    return sum(v * b_map.get(i, 0.0) for i, v in zip(a.indices, a.values, strict=True))


def _ranks(candidates: list, key) -> dict[int, float]:
    """Dense-rank candidates by `key` descending; equal scores share the same rank.

    Sharing ranks on ties avoids letting an incidental stable-sort order (e.g.
    when every score is 0.0, as with an empty sparse query) masquerade as a
    real signal in the RRF fusion.
    """
    scores = [key(c) for c in candidates]
    order = sorted(range(len(candidates)), key=lambda i: scores[i], reverse=True)
    ranks: dict[int, float] = {}
    rank = 0
    for pos, i in enumerate(order):
        if pos > 0 and scores[i] != scores[order[pos - 1]]:
            rank = pos
        ranks[i] = rank
    return ranks
