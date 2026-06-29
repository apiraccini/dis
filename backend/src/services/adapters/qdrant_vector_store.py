from __future__ import annotations

import uuid
from uuid import UUID

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qm

from src.repositories.protocols import ChunkPayload, SearchHit

__all__ = ['QdrantVectorStore']

# Fixed namespace so point ids derived from (document_id, chunk_index) are
# deterministic and reproducible across re-ingestion.
_NAMESPACE = uuid.UUID('a4c0c7b0-1f2e-4d3a-9b6c-8e1d2f3a4b5c')

# Payload field names (single source of truth).
F_DOCUMENT_ID = 'document_id'
F_DOCUMENT_NAME = 'document_name'
F_TAGS = 'tags'
F_CHUNK_INDEX = 'chunk_index'
F_TEXT = 'text'


class QdrantVectorStore:
    """VectorStore backed by Qdrant (async).

    - Collection is created on startup if absent (see `ensure_collection`).
    - upsert atomically replaces a document's chunks: delete-by-document then
      insert. A failure between the two surfaces to the ingestion failure path
      (no chunk_count is set).
    - search pushes tags (OR) and document_ids (membership) into the query as
      native payload filters; results are ranked by descending cosine
      similarity (Qdrant returns similarity as the score for COSINE distance).
    """

    def __init__(self, *, client: AsyncQdrantClient, collection: str) -> None:
        self._client = client
        self._collection = collection

    @staticmethod
    async def ensure_collection(client: AsyncQdrantClient, collection: str, dim: int) -> None:
        if await client.collection_exists(collection):
            return
        await client.create_collection(
            collection,
            vectors_config=qm.VectorParams(size=dim, distance=qm.Distance.COSINE),
        )
        # Payload indexes on the filtered fields. Without these, filtered HNSW
        # queries can't traverse filtered-out nodes and fall back to full-scan
        # filtering — see the qdrant-search-quality skill. Both fields are
        # keyword-typed (document_id is a string uuid; tags is a list of strings).
        await client.create_payload_index(collection, F_DOCUMENT_ID, qm.PayloadSchemaType.KEYWORD)
        await client.create_payload_index(collection, F_TAGS, qm.PayloadSchemaType.KEYWORD)

    async def provision(self, dim: int) -> None:
        """Ensure the collection exists with the right vector size (startup)."""
        await self.ensure_collection(self._client, self._collection, dim)

    # Deterministic point id for (document, chunk) so re-ingestion is idempotent.
    @staticmethod
    def _point_id(document_id: UUID, chunk_index: int) -> str:
        return str(uuid.uuid5(_NAMESPACE, f'{document_id}:{chunk_index}'))

    async def upsert(
        self,
        document_id: UUID,
        chunks: list[ChunkPayload],
        vectors: list[list[float]],
    ) -> None:
        await self._delete_by_document(document_id)
        points = [
            qm.PointStruct(
                id=self._point_id(document_id, ch.chunk_index),
                vector=vec,
                payload={
                    F_DOCUMENT_ID: str(document_id),
                    F_DOCUMENT_NAME: ch.document_name,
                    F_TAGS: list(ch.tags),
                    F_CHUNK_INDEX: ch.chunk_index,
                    F_TEXT: ch.text,
                },
            )
            for ch, vec in zip(chunks, vectors, strict=True)
        ]
        await self._client.upsert(self._collection, points=points)

    async def delete_by_document(self, document_id: UUID) -> None:
        await self._delete_by_document(document_id)

    async def _delete_by_document(self, document_id: UUID) -> None:
        await self._client.delete(
            self._collection,
            points_selector=qm.Filter(
                must=[
                    qm.FieldCondition(
                        key=F_DOCUMENT_ID,
                        match=qm.MatchValue(value=str(document_id)),
                    )
                ]
            ),
        )

    async def search(
        self,
        query: list[float],
        top_k: int,
        *,
        tags: list[str] | None = None,
        document_ids: list[UUID] | None = None,
    ) -> list[SearchHit]:
        must: list[qm.Condition] = []
        if tags:
            must.append(qm.FieldCondition(key=F_TAGS, match=qm.MatchAny(any=list(tags))))
        if document_ids:
            must.append(
                qm.FieldCondition(
                    key=F_DOCUMENT_ID,
                    match=qm.MatchAny(any=[str(d) for d in document_ids]),
                )
            )
        query_filter = qm.Filter(must=must) if must else None

        resp = await self._client.query_points(
            self._collection,
            query=query,
            query_filter=query_filter,
            limit=top_k,
            with_payload=True,
            with_vectors=False,
        )
        hits: list[SearchHit] = []
        for p in resp.points:
            payload = p.payload
            assert payload is not None  # with_payload=True always returns it
            hits.append(
                SearchHit(
                    document_id=UUID(payload[F_DOCUMENT_ID]),
                    document_name=payload[F_DOCUMENT_NAME],
                    tags=list(payload.get(F_TAGS, [])),
                    chunk_index=payload[F_CHUNK_INDEX],
                    text=payload[F_TEXT],
                    score=p.score,
                )
            )
        return hits
