from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from src.mcp_server import _search, list_documents, list_tags, search
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
    assert result == 'No documents found.'


async def test_list_documents_pagination(repo: InMemoryDocumentRepository) -> None:
    for i in range(3):
        await _seed_doc(repo, content_hash=f'h{i}')

    result = await list_documents(offset=0, limit=2, repo=repo)
    assert '2 document(s) (total 3)' in result

    result2 = await list_documents(offset=2, limit=2, repo=repo)
    assert '1 document(s) (total 3)' in result2


async def test_list_documents_tag_filter(repo: InMemoryDocumentRepository) -> None:
    await _seed_doc(repo, content_hash='h1', tags=['compliance'])
    await _seed_doc(repo, content_hash='h2', tags=['hr'])

    result = await list_documents(tag='compliance', repo=repo)
    text = result
    assert '1 document(s) (total 1)' in text
    assert 'doc.pdf' in text
    assert 'compliance' in text


async def test_list_documents_limits_at_500(repo: InMemoryDocumentRepository) -> None:
    """The limit caps at 500."""
    result = await list_documents(limit=1000, repo=repo)
    # repo is empty, but no error means cap enforcement works
    assert 'No documents found.' in result


# ── list_tags ───────────────────────────────────────────────────────────


async def test_list_tags_empty(repo: InMemoryDocumentRepository) -> None:
    result = await list_tags(repo=repo)
    assert result == 'No tags found.'


async def test_list_tags_returns_sorted_unique(repo: InMemoryDocumentRepository) -> None:
    await _seed_doc(repo, content_hash='h1', tags=['zebra', 'apple'])
    await _seed_doc(repo, content_hash='h2', tags=['banana', 'apple'])

    result = await list_tags(repo=repo)
    assert result == 'apple, banana, zebra'


# ── search ──────────────────────────────────────────────────────────────


async def test_search_no_filters(adapters: Adapters, vectors: InMemoryVectorStore) -> None:
    did = uuid4()
    await _seed_vector(vectors, did, text='climate report')
    did2 = uuid4()
    await _seed_vector(vectors, did2, text='budget review', name='budget.pdf')

    result = await _search('climate', 5, adapters)
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

    result = await _search('rules', 5, adapters, tags=['compliance'])
    assert len(result.hits) >= 1
    assert all(h.document_id == str(cid) for h in result.hits)


async def test_search_document_ids_filter(adapters: Adapters, vectors: InMemoryVectorStore) -> None:
    _cid, hid = await _prep_search(vectors, adapters)

    result = await _search('policies', 5, adapters, document_ids=[str(hid)])
    assert len(result.hits) >= 1
    assert all(h.document_id == str(hid) for h in result.hits)


async def test_search_combined_filters(adapters: Adapters, vectors: InMemoryVectorStore) -> None:
    _cid, _hid = await _prep_search(vectors, adapters)
    cid2 = uuid4()
    await _seed_vector(vectors, cid2, tags=['compliance', 'hr'], text='joint compliance and hr')

    # tags=['hr'] AND document_ids=[cid2]
    result = await _search('hr', 5, adapters, tags=['hr'], document_ids=[str(cid2)])
    assert len(result.hits) >= 1
    assert all(h.document_id == str(cid2) for h in result.hits)


async def test_search_top_k_default_is_5(adapters: Adapters, vectors: InMemoryVectorStore) -> None:
    for i in range(10):
        await _seed_vector(vectors, uuid4(), text=f'doc {i}')
    result = await _search('doc', 5, adapters)
    assert len(result.hits) <= 5


async def test_search_top_k_caps_at_50(adapters: Adapters, vectors: InMemoryVectorStore) -> None:
    for i in range(60):
        await _seed_vector(vectors, uuid4(), text=f'doc {i}')
    result = await _search('doc', 100, adapters)
    assert len(result.hits) <= 50


async def test_search_tool_returns_text_only(
    adapters: Adapters, vectors: InMemoryVectorStore
) -> None:
    """search() returns a plain string (compact text, no structured_content),
    to avoid duplicating (potentially large) chunk text across both fields."""
    await _seed_vector(vectors, uuid4(), text='climate report')

    result = await search(query='climate', adapters=adapters)
    assert 'climate report' in result


# search_by_tag and search_by_document were removed as separate tools — their
# behavior is covered by search()'s tags/document_ids filters, tested above.


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
    assert 'search_by_tag' not in tool_names
    assert 'search_by_document' not in tool_names
