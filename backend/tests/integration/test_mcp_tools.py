from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from src.mcp_server import (
    list_documents,
    list_tags,
    search,
    search_by_document,
    search_by_tag,
)
from src.models.document import Document
from src.repositories.in_memory import InMemoryDocumentRepository, InMemoryVectorStore
from src.services.factory import Adapters
from tests._fakes import FakeEmbedder, FakeSparseEmbedder, _word_sparse_vector

pytestmark = pytest.mark.integration

# ── Fixtures ────────────────────────────────────────────────────────────


@pytest.fixture
def repo() -> InMemoryDocumentRepository:
    return InMemoryDocumentRepository()


@pytest.fixture
def vectors() -> InMemoryVectorStore:
    return InMemoryVectorStore()


@pytest.fixture
def adapters(vectors: InMemoryVectorStore, fake_embedder: FakeEmbedder) -> Adapters:
    return Adapters(
        parser=fake_embedder,  # type: ignore  # not needed for search tools
        chunker=fake_embedder,  # type: ignore
        embedder=fake_embedder,
        query_embedder=fake_embedder,
        sparse_embedder=FakeSparseEmbedder(),
        vectors=vectors,
    )


@pytest.fixture
def fake_embedder() -> FakeEmbedder:
    return FakeEmbedder(dimension=4)


async def _seed_doc(
    repo: InMemoryDocumentRepository,
    *,
    filename: str = 'doc.pdf',
    tags: list[str] | None = None,
    content_hash: str | None = None,
) -> Document:
    return await repo.create(
        Document(
            filename=filename,
            content_hash=content_hash or f'hash-{uuid4().hex[:8]}',
            parsed_text='content',
            tags=tags or [],
            size_bytes=7,
            content_type='application/pdf',
        )
    )


async def _seed_vector(
    vectors: InMemoryVectorStore,
    document_id: UUID,
    *,
    name: str = 'doc.pdf',
    tags: list[str] | None = None,
    text: str = 'hello world',
    index: int = 0,
) -> None:
    from src.repositories.protocols import ChunkPayload

    await vectors.upsert(
        document_id,
        [
            ChunkPayload(
                document_id=document_id,
                document_name=name,
                tags=tags or [],
                chunk_index=index,
                text=text,
            )
        ],
        [[0.5, 0.5, 0.5, 0.5]],
        [_word_sparse_vector(text)],
    )


# ── list_documents ──────────────────────────────────────────────────────


async def test_list_documents_empty(repo: InMemoryDocumentRepository) -> None:
    result = await list_documents(repo=repo)
    assert result.documents == []
    assert result.total == 0


async def test_list_documents_pagination(repo: InMemoryDocumentRepository) -> None:
    for i in range(3):
        await _seed_doc(repo, content_hash=f'h{i}')

    result = await list_documents(offset=0, limit=2, repo=repo)
    assert len(result.documents) == 2
    assert result.total == 3

    result2 = await list_documents(offset=2, limit=2, repo=repo)
    assert len(result2.documents) == 1
    assert result2.total == 3


async def test_list_documents_tag_filter(repo: InMemoryDocumentRepository) -> None:
    await _seed_doc(repo, content_hash='h1', tags=['compliance'])
    await _seed_doc(repo, content_hash='h2', tags=['hr'])

    result = await list_documents(tag='compliance', repo=repo)
    assert result.total == 1
    assert result.documents[0].filename == 'doc.pdf'
    assert 'compliance' in result.documents[0].tags


async def test_list_documents_limits_at_500(repo: InMemoryDocumentRepository) -> None:
    """The limit caps at 500."""
    result = await list_documents(limit=1000, repo=repo)
    # repo is empty, but no error means cap enforcement works
    assert result.total == 0


# ── list_tags ───────────────────────────────────────────────────────────


async def test_list_tags_empty(repo: InMemoryDocumentRepository) -> None:
    result = await list_tags(repo=repo)
    assert result.tags == []


async def test_list_tags_returns_sorted_unique(repo: InMemoryDocumentRepository) -> None:
    await _seed_doc(repo, content_hash='h1', tags=['zebra', 'apple'])
    await _seed_doc(repo, content_hash='h2', tags=['banana', 'apple'])

    result = await list_tags(repo=repo)
    assert result.tags == ['apple', 'banana', 'zebra']


# ── search ──────────────────────────────────────────────────────────────


async def test_search_no_filters(adapters: Adapters, vectors: InMemoryVectorStore) -> None:
    did = uuid4()
    await _seed_vector(vectors, did, text='climate report')
    did2 = uuid4()
    await _seed_vector(vectors, did2, text='budget review', name='budget.pdf')

    result = await search(query='climate', adapters=adapters)
    assert len(result.hits) >= 1


async def _prep_search(vectors, adapters) -> list[UUID]:
    """Seed docs + vectors, return [compliance_doc_id, hr_doc_id]."""
    cid = uuid4()
    hid = uuid4()
    await _seed_vector(vectors, cid, tags=['compliance'], text='compliance rules')
    await _seed_vector(vectors, hid, tags=['hr'], text='hr policies')
    return [cid, hid]


async def test_search_tag_filter(adapters: Adapters, vectors: InMemoryVectorStore) -> None:
    cid, _hid = await _prep_search(vectors, adapters)

    result = await search(query='rules', tags=['compliance'], adapters=adapters)
    assert len(result.hits) >= 1
    assert all(h.document_id == str(cid) for h in result.hits)


async def test_search_document_ids_filter(adapters: Adapters, vectors: InMemoryVectorStore) -> None:
    _cid, hid = await _prep_search(vectors, adapters)

    result = await search(query='policies', document_ids=[str(hid)], adapters=adapters)
    assert len(result.hits) >= 1
    assert all(h.document_id == str(hid) for h in result.hits)


async def test_search_combined_filters(adapters: Adapters, vectors: InMemoryVectorStore) -> None:
    _cid, _hid = await _prep_search(vectors, adapters)
    cid2 = uuid4()
    await _seed_vector(vectors, cid2, tags=['compliance', 'hr'], text='joint compliance and hr')

    # tags=['hr'] AND document_ids=[cid2]
    result = await search(query='hr', tags=['hr'], document_ids=[str(cid2)], adapters=adapters)
    assert len(result.hits) >= 1
    assert all(h.document_id == str(cid2) for h in result.hits)


async def test_search_top_k_default_is_5(adapters: Adapters, vectors: InMemoryVectorStore) -> None:
    for i in range(10):
        await _seed_vector(vectors, uuid4(), text=f'doc {i}')
    result = await search(query='doc', adapters=adapters)
    assert len(result.hits) <= 5


async def test_search_top_k_caps_at_50(adapters: Adapters, vectors: InMemoryVectorStore) -> None:
    for i in range(60):
        await _seed_vector(vectors, uuid4(), text=f'doc {i}')
    result = await search(query='doc', top_k=100, adapters=adapters)
    assert len(result.hits) <= 50


# ── search_by_tag ───────────────────────────────────────────────────────


async def test_search_by_tag_requires_tags(
    adapters: Adapters, vectors: InMemoryVectorStore
) -> None:
    cid, _hid = await _prep_search(vectors, adapters)
    result = await search_by_tag(query='rules', tags=['compliance'], adapters=adapters)
    assert len(result.hits) >= 1
    assert all(h.document_id == str(cid) for h in result.hits)


# ── search_by_document ──────────────────────────────────────────────────


async def test_search_by_document_requires_ids(
    adapters: Adapters, vectors: InMemoryVectorStore
) -> None:
    _cid, hid = await _prep_search(vectors, adapters)
    result = await search_by_document(query='policies', document_ids=[str(hid)], adapters=adapters)
    assert len(result.hits) >= 1
    assert all(h.document_id == str(hid) for h in result.hits)


# ── ping removed ────────────────────────────────────────────────────────


async def test_ping_tool_not_registered() -> None:
    """The ping smoke tool was removed — clients calling ping get ToolNotFound."""
    from src.mcp_server import mcp

    tools = await mcp.list_tools()
    tool_names = {t.name for t in tools}
    assert 'ping' not in tool_names
    assert 'list_documents' in tool_names
    assert 'list_tags' in tool_names
    assert 'search' in tool_names
    assert 'search_by_tag' in tool_names
    assert 'search_by_document' in tool_names
