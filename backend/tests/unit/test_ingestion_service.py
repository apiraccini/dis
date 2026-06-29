from __future__ import annotations

import hashlib
from uuid import uuid4

import pytest

from src.models.document import Document, DocumentStatus
from src.repositories.in_memory import InMemoryDocumentRepository, InMemoryVectorStore
from src.services.ingestion import IngestionService
from src.services.protocols import Embedder
from tests._fakes import FakeChunker, FakeEmbedder, FakeParser

PARSED_TEXT = 'alpha bravo charlie delta echo'


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _make_service[E: Embedder](
    *,
    parsed_text: str = PARSED_TEXT,
    chunker: FakeChunker | None = None,
    embedder: E,
) -> tuple[
    IngestionService,
    FakeParser,
    FakeChunker,
    E,
    InMemoryDocumentRepository,
    InMemoryVectorStore,
]:
    parser = FakeParser(parsed_text)
    ch = chunker or FakeChunker(words_per_chunk=2)
    docs = InMemoryDocumentRepository()
    vectors = InMemoryVectorStore()
    service = IngestionService(
        parser=parser,
        chunker=ch,
        embedder=embedder,
        documents=docs,
        vectors=vectors,
    )
    return service, parser, ch, embedder, docs, vectors


async def test_prepare_dedup_hit_returns_existing_doc_without_parsing() -> None:
    service, parser, ch, emb, docs, vectors = _make_service(embedder=FakeEmbedder(dimension=4))
    raw_hash = hashlib.sha256(b'upload bytes').hexdigest()
    existing = Document(
        filename='old.pdf',
        content_hash=raw_hash,
        parsed_text=PARSED_TEXT,
        tags=['compliance'],
        size_bytes=99,
        content_type='application/pdf',
    )
    await docs.create(existing)

    result = await service.prepare(content=b'upload bytes', filename='new.pdf', tags=['hr'])

    assert result.id == existing.id
    assert result.content_hash == raw_hash
    # No expensive work ran — parser wasn't called because hash matched first.
    assert parser.calls == []
    assert ch.calls == []
    assert emb.calls == []
    # No vectors upserted.
    assert await vectors.search(query=[1.0], top_k=10) == []


async def test_prepare_dedup_miss_creates_processing_doc_with_raw_byte_hash() -> None:
    service, _, _, _, docs, _ = _make_service(embedder=FakeEmbedder(dimension=4))

    result = await service.prepare(
        content=b'raw upload bytes',
        filename='report.txt',
        tags=['Compliance', ' compliance ', 'HR'],
    )

    assert result.id is not None
    assert result.status == DocumentStatus.processing
    assert result.content_hash == hashlib.sha256(b'raw upload bytes').hexdigest()
    assert result.parsed_text == PARSED_TEXT
    assert result.tags == ['compliance', 'hr']  # normalized + deduped
    assert result.size_bytes == len(b'raw upload bytes')
    assert result.filename == 'report.txt'

    fetched = await docs.get_by_id(result.id)
    assert fetched is not None
    assert fetched.status == DocumentStatus.processing


async def test_finalize_happy_path_sets_ready_and_chunk_count() -> None:
    service, _, ch, emb, _docs, vectors = _make_service(embedder=FakeEmbedder(dimension=4))

    prepared = await service.prepare(content=b'data', filename='doc.txt', tags=['compliance'])

    result = await service.finalize(prepared.id)

    assert result.status == DocumentStatus.ready
    expected_chunks = ch.chunk(PARSED_TEXT)
    assert result.chunk_count == len(expected_chunks)
    # Expensive work ran.
    assert len(emb.calls) == 1
    assert len(emb.calls[0]) == len(expected_chunks)
    # Vectors stored.
    query_vector = emb.returns[0][0]
    hits = await vectors.search(query=query_vector, top_k=10)
    assert len(hits) == len(expected_chunks)
    assert all(h.document_id == prepared.id for h in hits)


async def test_finalize_upserts_chunk_records_with_filename_tags_and_indices() -> None:
    service, _, ch, emb, _docs, vectors = _make_service(embedder=FakeEmbedder(dimension=4))
    prepared = await service.prepare(
        content=b'data', filename='report.pdf', tags=['Compliance', 'HR']
    )

    await service.finalize(prepared.id)

    expected_chunks = ch.chunk(PARSED_TEXT)
    expected_vectors = emb.returns[0]
    query_vector = expected_vectors[0]
    hits = await vectors.search(query=query_vector, top_k=10)
    hits_by_index = {h.chunk_index: h for h in hits}

    assert set(hits_by_index) == set(range(len(expected_chunks)))
    for i in range(len(expected_chunks)):
        h = hits_by_index[i]
        assert h.document_id == prepared.id
        assert h.document_name == 'report.pdf'  # filename, not doc id
        assert h.tags == ['compliance', 'hr']  # normalized tags denormalized into payload
        assert h.text == expected_chunks[i]


async def test_finalize_embedder_failure_raises_and_does_not_upsert() -> None:
    """finalize raises without catching — status is managed by the caller."""
    from tests._failing_embedder import FailingEmbedder

    failing = FailingEmbedder(dimension=4, exc=RuntimeError('embedder exploded'))
    service, _, _, _, docs, vectors = _make_service(embedder=failing)
    prepared = await service.prepare(content=b'data', filename='doc.txt', tags=[])

    with pytest.raises(RuntimeError, match='embedder exploded'):
        await service.finalize(prepared.id)

    # Document stays in processing status (finalize does not set failed itself).
    doc = await docs.get_by_id(prepared.id)
    assert doc is not None
    assert doc.status == DocumentStatus.processing
    assert doc.chunk_count == 0
    # No vectors were upserted (upsert is atomic per document).
    assert await vectors.search(query=[1.0, 0.0, 0.0, 0.0], top_k=10) == []


async def test_ingest_full_pipeline_composes_prepare_and_finalize() -> None:
    service, _, ch, emb, docs, vectors = _make_service(embedder=FakeEmbedder(dimension=4))

    result = await service.ingest(content=b'full upload', filename='full.txt', tags=['x'])

    assert result.status == DocumentStatus.ready
    expected_chunks = ch.chunk(PARSED_TEXT)
    assert result.chunk_count == len(expected_chunks)
    # One document created and ready.
    rows, total = await docs.list_documents()
    assert total == 1
    assert rows[0].status == DocumentStatus.ready
    # Vectors searchable end-to-end.
    query_vector = emb.returns[0][0]
    hits = await vectors.search(query=query_vector, top_k=10)
    assert len(hits) == len(expected_chunks)
    assert all(h.document_name == 'full.txt' for h in hits)


async def test_ingest_dedup_skips_finalize() -> None:
    service, _, ch, emb, _, _ = _make_service(embedder=FakeEmbedder(dimension=4))

    first = await service.ingest(content=b'same bytes', filename='a.txt', tags=[])
    second = await service.ingest(content=b'same bytes', filename='b.txt', tags=[])

    assert second.id == first.id
    assert second.status == DocumentStatus.ready
    # Chunker called only once (first ingest); second was a dedup hit in prepare.
    assert len(ch.calls) == 1
    assert len(emb.calls) == 1


async def test_delete_document_removes_from_both_repo_and_vector_store() -> None:
    service, _, _, _, docs, vectors = _make_service(embedder=FakeEmbedder(dimension=4))

    prepared = await service.ingest(content=b'one', filename='doc.txt', tags=['compliance'])
    assert await docs.get_by_id(prepared.id) is not None
    assert await vectors.search(query=[1.0, 0.0, 0.0, 0.0], top_k=10) != []

    await service.delete_document(prepared.id)

    assert await docs.get_by_id(prepared.id) is None
    assert await vectors.search(query=[1.0, 0.0, 0.0, 0.0], top_k=10) == []


async def test_delete_document_raises_on_missing_document() -> None:
    from src.core.errors import DocumentNotFoundError

    service, _, _, _, _, _ = _make_service(embedder=FakeEmbedder(dimension=4))

    with pytest.raises(DocumentNotFoundError):
        await service.delete_document(uuid4())


async def test_finalize_from_background_task_catches_exception_and_sets_failed() -> None:
    """When finalize is called from a background task (no supervisor), exceptions
    must be caught so they don't crash the server, and the doc status must be set to failed."""
    from tests._failing_embedder import FailingEmbedder

    failing = FailingEmbedder(dimension=4, exc=RuntimeError('embedder exploded'))
    service, _, _, _, docs, vectors = _make_service(embedder=failing)
    prepared = await service.prepare(content=b'data', filename='doc.txt', tags=[])
    assert prepared.status == DocumentStatus.processing

    # No exception should escape — it's a background task call
    await service.finalize_safe(prepared.id)

    failed = await docs.get_by_id(prepared.id)
    assert failed is not None
    assert failed.status == DocumentStatus.failed
    assert 'embedder exploded' in (failed.error_message or '')
    # No vectors were upserted
    assert await vectors.search(query=[1.0, 0.0, 0.0, 0.0], top_k=10) == []


async def test_cleanup_zombies_marks_processing_docs_as_failed() -> None:
    docs = InMemoryDocumentRepository()
    from src.services.ingestion import cleanup_zombies

    ready_doc = Document(
        id=uuid4(),
        filename='ready.pdf',
        content_hash=_hash('ready'),
        parsed_text='ready',
        status=DocumentStatus.ready,
    )
    processing_doc = Document(
        id=uuid4(),
        filename='processing.pdf',
        content_hash=_hash('processing'),
        parsed_text='processing',
        status=DocumentStatus.processing,
    )
    failed_doc = Document(
        id=uuid4(),
        filename='failed.pdf',
        content_hash=_hash('failed'),
        parsed_text='failed',
        status=DocumentStatus.failed,
    )
    for d in [ready_doc, processing_doc, failed_doc]:
        await docs.create(d)

    await cleanup_zombies(docs)

    ready_fetched = await docs.get_by_id(ready_doc.id)
    assert ready_fetched is not None
    assert ready_fetched.status == DocumentStatus.ready

    failed_fetched = await docs.get_by_id(failed_doc.id)
    assert failed_fetched is not None
    assert failed_fetched.status == DocumentStatus.failed

    cleaned = await docs.get_by_id(processing_doc.id)
    assert cleaned is not None
    assert cleaned.status == DocumentStatus.failed
    assert cleaned.error_message == 'Application restart while processing'
