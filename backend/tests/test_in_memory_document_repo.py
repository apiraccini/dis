from uuid import UUID, uuid4

import pytest

from src.core.errors import DocumentNotFoundError, DuplicateDocumentError
from src.models.document import Document, DocumentStatus
from src.repositories.in_memory import InMemoryDocumentRepository


def _doc(
    *,
    content_hash: str | None = None,
    filename: str = 'doc.pdf',
    tags: list[str] | None = None,
    parsed_text: str = 'hello world',
) -> Document:
    return Document(
        filename=filename,
        content_hash=content_hash or f'hash-{uuid4().hex[:8]}',
        parsed_text=parsed_text,
        tags=tags or [],
        size_bytes=len(parsed_text.encode()),
        content_type='application/pdf',
    )


@pytest.fixture
def repo() -> InMemoryDocumentRepository:
    return InMemoryDocumentRepository()


async def test_create_and_get_by_id_roundtrip(repo: InMemoryDocumentRepository) -> None:
    doc = _doc(tags=['Compliance', ' HR '])
    created = await repo.create(doc)

    assert isinstance(created.id, UUID)
    fetched = await repo.get_by_id(created.id)
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.filename == 'doc.pdf'
    # tags normalized on the stored document
    assert fetched.tags == ['compliance', 'hr']


async def test_create_assigns_id_when_none(repo: InMemoryDocumentRepository) -> None:
    doc = _doc()
    created = await repo.create(doc)
    assert created.id is not None
    assert doc.id == created.id  # same instance updated


async def test_create_duplicate_hash_raises(repo: InMemoryDocumentRepository) -> None:
    await repo.create(_doc(content_hash='same-hash'))
    with pytest.raises(DuplicateDocumentError):
        await repo.create(_doc(content_hash='same-hash', filename='other.pdf'))


async def test_get_by_id_missing_returns_none(repo: InMemoryDocumentRepository) -> None:
    assert await repo.get_by_id(uuid4()) is None


async def test_get_by_hash(repo: InMemoryDocumentRepository) -> None:
    created = await repo.create(_doc(content_hash='h1'))
    fetched = await repo.get_by_hash('h1')
    assert fetched is not None
    assert fetched.id == created.id


async def test_get_by_hash_missing_returns_none(repo: InMemoryDocumentRepository) -> None:
    assert await repo.get_by_hash('nope') is None


async def test_list_returns_all_with_total(repo: InMemoryDocumentRepository) -> None:
    for i in range(3):
        await repo.create(_doc(content_hash=f'h{i}'))
    rows, total = await repo.list_documents()
    assert total == 3
    assert len(rows) == 3


async def test_list_paginates_with_offset_and_limit(repo: InMemoryDocumentRepository) -> None:
    for i in range(5):
        await repo.create(_doc(content_hash=f'h{i}'))
    rows, total = await repo.list_documents(offset=1, limit=2)
    assert total == 5
    assert len(rows) == 2


async def test_list_filters_by_tag(repo: InMemoryDocumentRepository) -> None:
    await repo.create(_doc(content_hash='h1', tags=['compliance']))
    await repo.create(_doc(content_hash='h2', tags=['hr']))
    await repo.create(_doc(content_hash='h3', tags=['compliance', 'hr']))
    await repo.create(_doc(content_hash='h4', tags=['product']))

    rows, total = await repo.list_documents(tag='compliance')
    assert total == 2
    assert {r.content_hash for r in rows} == {'h1', 'h3'}


async def test_list_tag_filter_is_case_insensitive(repo: InMemoryDocumentRepository) -> None:
    await repo.create(_doc(content_hash='h1', tags=['Compliance']))
    rows, total = await repo.list_documents(tag='COMPLIANCE')
    assert total == 1
    assert rows[0].content_hash == 'h1'


async def test_update_status(repo: InMemoryDocumentRepository) -> None:
    created = await repo.create(_doc())
    updated = await repo.update_status(created.id, DocumentStatus.ready)
    assert updated.status == DocumentStatus.ready


async def test_update_status_sets_error_message_on_failed(repo: InMemoryDocumentRepository) -> None:
    created = await repo.create(_doc())
    updated = await repo.update_status(created.id, DocumentStatus.failed, error_message='boom')
    assert updated.status == DocumentStatus.failed
    assert updated.error_message == 'boom'


async def test_update_status_missing_raises(repo: InMemoryDocumentRepository) -> None:
    with pytest.raises(DocumentNotFoundError):
        await repo.update_status(uuid4(), DocumentStatus.ready)


async def test_update_chunk_count(repo: InMemoryDocumentRepository) -> None:
    created = await repo.create(_doc())
    assert created.chunk_count == 0
    updated = await repo.update_chunk_count(created.id, 42)
    assert updated.chunk_count == 42


async def test_update_chunk_count_missing_raises(repo: InMemoryDocumentRepository) -> None:
    with pytest.raises(DocumentNotFoundError):
        await repo.update_chunk_count(uuid4(), 1)


async def test_delete_removes_document(repo: InMemoryDocumentRepository) -> None:
    created = await repo.create(_doc())
    await repo.delete(created.id)
    assert await repo.get_by_id(created.id) is None


async def test_delete_missing_raises(repo: InMemoryDocumentRepository) -> None:
    with pytest.raises(DocumentNotFoundError):
        await repo.delete(uuid4())
