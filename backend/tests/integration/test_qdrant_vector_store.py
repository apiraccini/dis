from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from qdrant_client.http import models as qm

from src.repositories.protocols import (
    ChunkPayload,
    SparseVector,
    VectorStore,
)
from src.services.adapters.qdrant_vector_store import QdrantVectorStore

pytestmark = pytest.mark.integration

DOC_ID = UUID('11111111-1111-1111-1111-111111111111')


def _chunks(n: int) -> list[ChunkPayload]:
    return [
        ChunkPayload(
            document_id=DOC_ID,
            document_name='report.pdf',
            tags=['compliance', 'finance'],
            chunk_index=i,
            text=f'chunk {i} text',
        )
        for i in range(n)
    ]


def _vecs(n: int, dim: int = 4) -> list[list[float]]:
    return [[float(i)] * dim for i in range(n)]


def _sparse_vecs(n: int) -> list[SparseVector]:
    return [SparseVector(indices=[i], values=[1.0]) for i in range(n)]


def test_satisfies_vector_store_protocol() -> None:
    store = QdrantVectorStore(client=AsyncMock(), collection='documents')
    assert isinstance(store, VectorStore)


async def test_ensure_collection_creates_named_vectors_and_payload_indexes_when_absent() -> None:
    client = AsyncMock()
    client.collection_exists.return_value = False

    await QdrantVectorStore.ensure_collection(client, 'documents', dim=1536)

    client.collection_exists.assert_awaited_once_with('documents')
    client.create_collection.assert_awaited_once()
    kwargs = client.create_collection.call_args.kwargs
    assert kwargs['vectors_config']['dense'].size == 1536
    assert kwargs['vectors_config']['dense'].distance == qm.Distance.COSINE
    assert 'sparse' in kwargs['sparse_vectors_config']
    # Payload indexes on the two filtered fields (document_id, tags).
    indexed_fields = {c.args[1] for c in client.create_payload_index.call_args_list}
    assert indexed_fields == {'document_id', 'tags'}
    for c in client.create_payload_index.call_args_list:
        assert c.args[2] == qm.PayloadSchemaType.KEYWORD


async def test_ensure_collection_idempotent_when_present() -> None:
    client = AsyncMock()
    client.collection_exists.return_value = True

    await QdrantVectorStore.ensure_collection(client, 'documents', dim=1536)

    client.create_collection.assert_not_awaited()
    client.create_payload_index.assert_not_awaited()


async def test_upsert_deletes_existing_then_inserts_with_named_vectors_and_payload() -> None:
    client = AsyncMock()
    store = QdrantVectorStore(client=client, collection='documents')

    await store.upsert(DOC_ID, _chunks(2), _vecs(2), _sparse_vecs(2))

    # Delete (clear old chunks) happens before insert.
    assert client.method_calls[0][0] == 'delete'
    assert client.method_calls[1][0] == 'upsert'
    # Delete targets this document_id.
    delete_filter = client.method_calls[0].kwargs['points_selector']
    assert delete_filter.must[0].key == 'document_id'
    assert delete_filter.must[0].match.value == str(DOC_ID)
    # Upsert carries one point per chunk with both named vectors + full payload.
    points = client.upsert.call_args.kwargs['points']
    assert len(points) == 2
    p0 = points[0]
    assert p0.vector['dense'] == [0.0, 0.0, 0.0, 0.0]
    assert p0.vector['sparse'].indices == [0]
    assert p0.vector['sparse'].values == [1.0]
    assert p0.payload['document_id'] == str(DOC_ID)
    assert p0.payload['document_name'] == 'report.pdf'
    assert p0.payload['tags'] == ['compliance', 'finance']
    assert p0.payload['chunk_index'] == 0
    assert p0.payload['text'] == 'chunk 0 text'
    # Point ids are stable UUIDs (re-upserting the same chunks yields the same ids).
    assert [p.id for p in points] == [
        QdrantVectorStore._point_id(DOC_ID, 0),
        QdrantVectorStore._point_id(DOC_ID, 1),
    ]


async def test_search_fuses_dense_and_sparse_prefetch_via_rrf() -> None:
    client = AsyncMock()
    client.query_points.return_value = SimpleNamespace(
        points=[
            SimpleNamespace(
                id='x',
                score=0.9,
                payload={
                    'document_id': str(DOC_ID),
                    'document_name': 'report.pdf',
                    'tags': ['compliance'],
                    'chunk_index': 0,
                    'text': 'first',
                },
            ),
            SimpleNamespace(
                id='y',
                score=0.7,
                payload={
                    'document_id': str(DOC_ID),
                    'document_name': 'report.pdf',
                    'tags': ['compliance'],
                    'chunk_index': 1,
                    'text': 'second',
                },
            ),
        ]
    )
    store = QdrantVectorStore(client=client, collection='documents')
    sparse_query = SparseVector(indices=[1, 2], values=[0.5, 0.5])

    hits = await store.search(
        [0.1] * 4,
        sparse_query,
        top_k=5,
        tags=['compliance'],
        document_ids=[DOC_ID],
    )

    assert len(hits) == 2
    assert hits[0].score == 0.9
    assert hits[0].text == 'first'
    assert hits[0].document_id == DOC_ID
    assert hits[0].tags == ['compliance']
    assert hits[1].chunk_index == 1

    call_kwargs = client.query_points.call_args.kwargs
    assert isinstance(call_kwargs['query'], qm.FusionQuery)
    assert call_kwargs['query'].fusion == qm.Fusion.RRF
    prefetches = call_kwargs['prefetch']
    assert len(prefetches) == 2
    dense_pf = next(p for p in prefetches if p.using == 'dense')
    sparse_pf = next(p for p in prefetches if p.using == 'sparse')
    assert dense_pf.query == [0.1] * 4
    assert sparse_pf.query.indices == [1, 2]
    # The tags/document_ids filter is pushed into both prefetches.
    for pf in prefetches:
        keys = {c.key for c in pf.filter.must}
        assert keys == {'tags', 'document_id'}
    # top_k is pushed as the final fused query limit.
    assert call_kwargs['limit'] == 5


async def test_search_without_filters_passes_none_filter_on_prefetches() -> None:
    client = AsyncMock()
    client.query_points.return_value = SimpleNamespace(points=[])
    store = QdrantVectorStore(client=client, collection='documents')

    await store.search([0.1] * 4, SparseVector(indices=[], values=[]), top_k=5)

    prefetches = client.query_points.call_args.kwargs['prefetch']
    assert all(pf.filter is None for pf in prefetches)


async def test_delete_by_document_sends_document_id_filter() -> None:
    client = AsyncMock()
    store = QdrantVectorStore(client=client, collection='documents')

    await store.delete_by_document(DOC_ID)

    flt = client.delete.call_args.kwargs['points_selector']
    assert flt.must[0].key == 'document_id'
    assert flt.must[0].match.value == str(DOC_ID)
