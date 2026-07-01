from uuid import uuid4

from src.repositories.in_memory import InMemoryVectorStore
from src.repositories.protocols import ChunkPayload, SearchHit, SparseVector, VectorStore


def _chunk(
    document_id, name='doc.pdf', tags=('compliance',), index=0, text='hello'
) -> ChunkPayload:
    return ChunkPayload(
        document_id=document_id,
        document_name=name,
        tags=list(tags),
        chunk_index=index,
        text=text,
    )


def _sparse(*indices: int) -> SparseVector:
    # Simple unweighted sparse vector: one "term" per index, all equal weight.
    return SparseVector(indices=list(indices), values=[1.0] * len(indices))


def _empty_sparse() -> SparseVector:
    return SparseVector(indices=[], values=[])


def test_inmemory_vector_store_satisfies_protocol() -> None:
    assert isinstance(InMemoryVectorStore(), VectorStore)


async def test_upsert_stores_chunks_and_vectors_by_document() -> None:
    store = InMemoryVectorStore()
    doc_id = uuid4()
    chunks = [_chunk(doc_id, index=0), _chunk(doc_id, index=1)]
    vectors = [[1.0, 0.0], [0.0, 1.0]]
    sparse = [_empty_sparse(), _empty_sparse()]

    await store.upsert(doc_id, chunks, vectors, sparse)

    hits = await store.search(query=[1.0, 0.0], sparse_query=_empty_sparse(), top_k=10)
    assert len(hits) == 2
    assert all(isinstance(h, SearchHit) for h in hits)
    assert {h.chunk_index for h in hits} == {0, 1}
    assert all(h.document_id == doc_id for h in hits)


async def test_search_returns_top_k_ranked_by_descending_similarity() -> None:
    store = InMemoryVectorStore()
    doc_id = uuid4()
    # three vectors at varying angles to the query [1.0, 0.0]; no lexical signal.
    await store.upsert(
        doc_id,
        [
            _chunk(doc_id, index=0, text='orthogonal'),
            _chunk(doc_id, index=1, text='identical'),
            _chunk(doc_id, index=2, text='opposite'),
        ],
        [[0.0, 1.0], [1.0, 0.0], [-1.0, 0.0]],
        [_empty_sparse(), _empty_sparse(), _empty_sparse()],
    )

    hits = await store.search(query=[1.0, 0.0], sparse_query=_empty_sparse(), top_k=2)

    assert len(hits) == 2
    assert hits[0].chunk_index == 1  # cosine 1.0
    assert hits[1].chunk_index == 0  # cosine 0.0; opposite (-1.0) ranks last, excluded
    assert hits[0].score > hits[1].score


async def test_keyword_match_outranks_weak_dense_similarity_via_fusion() -> None:
    store = InMemoryVectorStore()
    doc_id = uuid4()
    query_vec = [1.0, 0.0]
    query_sparse = _sparse(42)
    # chunk 0 ("best"): top dense match, no lexical overlap with the query.
    # chunk 1 ("second"): close second on dense, and the only chunk sharing the
    #                      query's sparse term (so it wins the sparse ranking outright).
    # chunk 2 ("distractor"): weakest dense match, no lexical overlap either.
    await store.upsert(
        doc_id,
        [
            _chunk(doc_id, index=0, text='best'),
            _chunk(doc_id, index=1, text='second'),
            _chunk(doc_id, index=2, text='distractor'),
        ],
        [[1.0, 0.0], [0.99, 0.14], [0.5, 0.86]],
        [_empty_sparse(), _sparse(42), _empty_sparse()],
    )

    dense_only_hits = await store.search(query=query_vec, sparse_query=_empty_sparse(), top_k=3)
    assert dense_only_hits[0].chunk_index == 0  # pure dense ranks the top cosine match first

    fused_hits = await store.search(query=query_vec, sparse_query=query_sparse, top_k=3)
    # chunk 1 is a close dense second AND the sole sparse match, so fusion lifts
    # it to at least tie the pure-dense leader (chunk 0), unlike dense-only search.
    top_two = {fused_hits[0].chunk_index, fused_hits[1].chunk_index}
    assert top_two == {0, 1}
    assert fused_hits[0].chunk_index == 1 or fused_hits[0].score == fused_hits[1].score


async def test_search_filters_by_tags_with_or_semantics() -> None:
    store = InMemoryVectorStore()
    compliance_doc = uuid4()
    hr_doc = uuid4()
    product_doc = uuid4()
    await store.upsert(
        compliance_doc,
        [_chunk(compliance_doc, index=0, tags=['compliance'])],
        [[1.0]],
        [_empty_sparse()],
    )
    await store.upsert(hr_doc, [_chunk(hr_doc, index=0, tags=['hr'])], [[1.0]], [_empty_sparse()])
    await store.upsert(
        product_doc, [_chunk(product_doc, index=0, tags=['product'])], [[1.0]], [_empty_sparse()]
    )

    hits = await store.search(
        query=[1.0], sparse_query=_empty_sparse(), top_k=10, tags=['compliance', 'hr']
    )

    returned_ids = {h.document_id for h in hits}
    assert returned_ids == {compliance_doc, hr_doc}
    assert product_doc not in returned_ids


async def test_search_tag_filter_is_case_insensitive() -> None:
    store = InMemoryVectorStore()
    doc_id = uuid4()
    await store.upsert(
        doc_id, [_chunk(doc_id, index=0, tags=['Compliance'])], [[1.0]], [_empty_sparse()]
    )

    hits = await store.search(
        query=[1.0], sparse_query=_empty_sparse(), top_k=10, tags=['COMPLIANCE']
    )

    assert len(hits) == 1
    assert hits[0].document_id == doc_id


async def test_search_filters_by_document_ids() -> None:
    store = InMemoryVectorStore()
    keep = uuid4()
    drop = uuid4()
    await store.upsert(keep, [_chunk(keep, index=0)], [[1.0]], [_empty_sparse()])
    await store.upsert(drop, [_chunk(drop, index=0)], [[1.0]], [_empty_sparse()])

    hits = await store.search(
        query=[1.0], sparse_query=_empty_sparse(), top_k=10, document_ids=[keep]
    )

    assert {h.document_id for h in hits} == {keep}


async def test_upsert_replaces_prior_chunks_for_document() -> None:
    store = InMemoryVectorStore()
    doc_id = uuid4()
    await store.upsert(
        doc_id,
        [_chunk(doc_id, index=0), _chunk(doc_id, index=1)],
        [[1.0], [1.0]],
        [_empty_sparse(), _empty_sparse()],
    )

    await store.upsert(
        doc_id, [_chunk(doc_id, index=0, text='replaced')], [[0.5]], [_empty_sparse()]
    )

    hits = await store.search(query=[0.5], sparse_query=_empty_sparse(), top_k=10)
    assert len(hits) == 1
    assert hits[0].text == 'replaced'


async def test_delete_by_document_removes_its_chunks() -> None:
    store = InMemoryVectorStore()
    doc_id = uuid4()
    await store.upsert(doc_id, [_chunk(doc_id, index=0)], [[1.0]], [_empty_sparse()])

    await store.delete_by_document(doc_id)

    assert await store.search(query=[1.0], sparse_query=_empty_sparse(), top_k=10) == []
