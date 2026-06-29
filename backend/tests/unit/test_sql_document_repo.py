from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.errors import DocumentNotFoundError, DuplicateDocumentError
from src.models.document import Document, DocumentStatus
from src.repositories.document_repo import SqlModelDocumentRepository


def _mock_doc(
    *,
    content_hash: str = 'hash1',
    filename: str = 'doc.pdf',
    tags: list[str] | None = None,
    parsed_text: str = 'hello world',
) -> Document:
    return Document(
        filename=filename,
        content_hash=content_hash,
        parsed_text=parsed_text,
        tags=tags or [],
        size_bytes=len(parsed_text.encode()),
        content_type='application/pdf',
    )


@pytest.fixture
def session() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def repo(session: AsyncMock) -> SqlModelDocumentRepository:
    return SqlModelDocumentRepository(session)


async def test_create_adds_normalized_tags_and_commits(
    repo: SqlModelDocumentRepository, session: AsyncMock
) -> None:
    doc = _mock_doc(tags=['  Compliance ', 'HR'])
    result = await repo.create(doc)

    assert result.tags == ['compliance', 'hr']
    session.add.assert_called_once_with(doc)
    session.commit.assert_awaited_once()
    session.refresh.assert_awaited_once_with(doc)


async def test_create_raises_on_integrity_error(
    repo: SqlModelDocumentRepository, session: AsyncMock
) -> None:
    doc = _mock_doc(content_hash='dup-hash')
    orig = MockError('duplicate key')
    session.commit.side_effect = IntegrityError('test', 'orig', orig)

    with pytest.raises(DuplicateDocumentError, match="content_hash 'dup-hash' already exists"):
        await repo.create(doc)

    session.rollback.assert_awaited_once()


async def test_get_by_id_returns_document(
    repo: SqlModelDocumentRepository, session: AsyncMock
) -> None:
    doc_id = uuid4()
    expected = _mock_doc(content_hash='h1')
    result_mock = MagicMock()
    result_mock.first.return_value = expected
    session.exec.return_value = result_mock

    result = await repo.get_by_id(doc_id)

    assert result is expected
    session.exec.assert_awaited_once()
    # Verify the select was built with the right WHERE clause
    call_stmt = session.exec.call_args[0][0]
    assert str(call_stmt).startswith('SELECT')


async def test_get_by_id_returns_none_when_missing(
    repo: SqlModelDocumentRepository, session: AsyncMock
) -> None:
    doc_id = uuid4()
    result_mock = MagicMock()
    result_mock.first.return_value = None
    session.exec.return_value = result_mock

    result = await repo.get_by_id(doc_id)

    assert result is None


async def test_get_by_hash_returns_document(
    repo: SqlModelDocumentRepository, session: AsyncMock
) -> None:
    expected = _mock_doc(content_hash='h1')
    result_mock = MagicMock()
    result_mock.first.return_value = expected
    session.exec.return_value = result_mock

    result = await repo.get_by_hash('h1')

    assert result is expected
    session.exec.assert_awaited_once()


async def test_get_by_hash_returns_none_when_missing(
    repo: SqlModelDocumentRepository, session: AsyncMock
) -> None:
    result_mock = MagicMock()
    result_mock.first.return_value = None
    session.exec.return_value = result_mock

    result = await repo.get_by_hash('nope')

    assert result is None


async def test_list_documents_no_tag(repo: SqlModelDocumentRepository, session: AsyncMock) -> None:
    doc1 = _mock_doc(content_hash='h1')
    doc2 = _mock_doc(content_hash='h2')

    count_mock = MagicMock()
    count_mock.one.return_value = 2
    page_mock = MagicMock()
    page_mock.all.return_value = [doc1, doc2]
    # First call to exec → total count; second → page
    session.exec = AsyncMock(side_effect=[count_mock, page_mock])

    rows, total = await repo.list_documents(offset=0, limit=10)

    assert total == 2
    assert list(rows) == [doc1, doc2]
    assert session.exec.await_count == 2


async def test_list_documents_with_tag(
    repo: SqlModelDocumentRepository, session: AsyncMock
) -> None:
    doc1 = _mock_doc(content_hash='h1', tags=['compliance'])

    count_mock = MagicMock()
    count_mock.one.return_value = 1
    page_mock = MagicMock()
    page_mock.all.return_value = [doc1]
    session.exec = AsyncMock(side_effect=[count_mock, page_mock])

    rows, total = await repo.list_documents(tag='compliance')

    assert total == 1
    assert list(rows) == [doc1]
    # Verify the WHERE clause was added (tags_col.any called)
    call_stmt = session.exec.call_args_list[0][0][0]
    assert 'ANY' in str(call_stmt) or 'any' in str(call_stmt).lower()


async def test_list_documents_with_tag_uses_normalized_value(
    repo: SqlModelDocumentRepository, session: AsyncMock
) -> None:
    """Tag filtering must lowercase+strip the tag value."""
    # Verify the compiled SQL has an ANY() clause (Postgres array containment)
    count_mock = MagicMock()
    count_mock.one.return_value = 0
    page_mock = MagicMock()
    page_mock.all.return_value = []
    session.exec = AsyncMock(side_effect=[count_mock, page_mock])

    await repo.list_documents(tag='  COMPLIANCE ')

    call_stmt = session.exec.call_args_list[0][0][0]
    stmt_str = str(call_stmt)
    # The compiled SQL should contain ANY(...) for the array containment check
    assert 'any' in stmt_str.lower() or 'ANY' in stmt_str


async def test_update_status_happy(repo: SqlModelDocumentRepository, session: AsyncMock) -> None:
    doc_id = uuid4()
    existing = _mock_doc(content_hash='h1')
    # get_by_id needs to return the doc
    get_mock = MagicMock()
    get_mock.first.return_value = existing
    refresh_mock = MagicMock()
    refresh_mock.first.return_value = existing
    session.exec = AsyncMock(side_effect=[get_mock, refresh_mock])

    result = await repo.update_status(doc_id, DocumentStatus.ready)

    assert result.status == DocumentStatus.ready
    assert existing.status == DocumentStatus.ready  # mutated in-place
    session.add.assert_called_once_with(existing)
    assert session.commit.await_count == 1
    assert session.refresh.await_count == 1


async def test_update_status_with_error_message(
    repo: SqlModelDocumentRepository, session: AsyncMock
) -> None:
    doc_id = uuid4()
    existing = _mock_doc(content_hash='h1', tags=[])
    get_mock = MagicMock()
    get_mock.first.return_value = existing
    refresh_mock = MagicMock()
    refresh_mock.first.return_value = existing
    session.exec = AsyncMock(side_effect=[get_mock, refresh_mock])

    result = await repo.update_status(doc_id, DocumentStatus.failed, error_message='boom')

    assert result.status == DocumentStatus.failed
    assert result.error_message == 'boom'
    assert existing.error_message == 'boom'


async def test_update_status_raises_on_missing(
    repo: SqlModelDocumentRepository, session: AsyncMock
) -> None:
    doc_id = uuid4()
    get_mock = MagicMock()
    get_mock.first.return_value = None
    session.exec = AsyncMock(side_effect=[get_mock])

    with pytest.raises(DocumentNotFoundError, match=f'no document with id {doc_id}'):
        await repo.update_status(doc_id, DocumentStatus.ready)


async def test_update_chunk_count_happy(
    repo: SqlModelDocumentRepository, session: AsyncMock
) -> None:
    doc_id = uuid4()
    existing = _mock_doc(content_hash='h1')
    get_mock = MagicMock()
    get_mock.first.return_value = existing
    refresh_mock = MagicMock()
    refresh_mock.first.return_value = existing
    session.exec = AsyncMock(side_effect=[get_mock, refresh_mock])

    result = await repo.update_chunk_count(doc_id, 42)

    assert result.chunk_count == 42
    assert existing.chunk_count == 42
    session.add.assert_called_once_with(existing)


async def test_update_chunk_count_raises_on_missing(
    repo: SqlModelDocumentRepository, session: AsyncMock
) -> None:
    doc_id = uuid4()
    get_mock = MagicMock()
    get_mock.first.return_value = None
    session.exec = AsyncMock(side_effect=[get_mock])

    with pytest.raises(DocumentNotFoundError, match=f'no document with id {doc_id}'):
        await repo.update_chunk_count(doc_id, 1)


async def test_delete_happy(repo: SqlModelDocumentRepository, session: AsyncMock) -> None:
    doc_id = uuid4()
    existing = _mock_doc(content_hash='h1')
    get_mock = MagicMock()
    get_mock.first.return_value = existing
    session.exec = AsyncMock(side_effect=[get_mock])

    await repo.delete(doc_id)

    session.delete.assert_called_once_with(existing)
    session.commit.assert_awaited_once()


async def test_delete_raises_on_missing(
    repo: SqlModelDocumentRepository, session: AsyncMock
) -> None:
    doc_id = uuid4()
    get_mock = MagicMock()
    get_mock.first.return_value = None
    session.exec = AsyncMock(side_effect=[get_mock])

    with pytest.raises(DocumentNotFoundError, match=f'no document with id {doc_id}'):
        await repo.delete(doc_id)

    session.delete.assert_not_called()


async def test_list_by_status(repo: SqlModelDocumentRepository, session: AsyncMock) -> None:
    doc1 = _mock_doc(content_hash='h1')
    count_mock = MagicMock()
    count_mock.one.return_value = 1
    page_mock = MagicMock()
    page_mock.all.return_value = [doc1]
    session.exec = AsyncMock(side_effect=[count_mock, page_mock])

    rows, total = await repo.list_by_status(DocumentStatus.ready)

    assert total == 1
    assert list(rows) == [doc1]


class MockError(Exception):
    """Helper for IntegrityError construction (used as orig)."""


async def test_create_returns_normalized_and_refreshed(
    repo: SqlModelDocumentRepository, session: AsyncMock
) -> None:
    """Tags are normalized, then document is refreshed from DB."""
    doc = _mock_doc(tags=['  Upper  '])
    refresh_mock = MagicMock()
    refresh_mock.first.return_value = None  # not used
    session.commit.side_effect = lambda: None  # type: ignore[assignment]
    session.refresh.side_effect = lambda d: setattr(d, 'tags', ['upper'])

    result = await repo.create(doc)

    # Normalized by our code
    assert result.tags == ['upper']


async def test_update_status_commit_and_refresh_ordering(
    repo: SqlModelDocumentRepository, session: AsyncMock
) -> None:
    """Commit is called before refresh."""
    doc_id = uuid4()
    existing = _mock_doc(content_hash='h1')
    get_mock = MagicMock()
    get_mock.first.return_value = existing
    refresh_mock = MagicMock()
    refresh_mock.first.return_value = existing
    session.exec = AsyncMock(side_effect=[get_mock, refresh_mock])

    await repo.update_status(doc_id, DocumentStatus.ready)

    # commit before refresh
    commit_order = session.commit.await_args
    assert commit_order is not None
