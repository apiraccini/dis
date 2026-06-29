from __future__ import annotations

from uuid import UUID

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.errors import DocumentNotFoundError, DuplicateDocumentError
from src.models.document import Document, DocumentStatus, normalize_tags

__all__ = ['SqlModelDocumentRepository']


class SqlModelDocumentRepository:
    """Async document store backed by SQLModel + an AsyncSession."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, document: Document) -> Document:
        document.tags = normalize_tags(document.tags)
        self._session.add(document)
        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise DuplicateDocumentError(
                f'document with content_hash {document.content_hash!r} already exists'
            ) from exc
        await self._session.refresh(document)
        return document

    async def get_by_id(self, document_id: UUID) -> Document | None:
        result = await self._session.exec(select(Document).where(Document.id == document_id))
        return result.first()

    async def get_by_hash(self, content_hash: str) -> Document | None:
        result = await self._session.exec(
            select(Document).where(Document.content_hash == content_hash)
        )
        return result.first()

    async def list_documents(
        self,
        offset: int = 0,
        limit: int = 100,
        tag: str | None = None,
    ) -> tuple[list[Document], int]:
        tag_norm = tag.strip().lower() if tag else None
        stmt = select(Document)
        if tag_norm is not None:
            # Postgres array-containment via ARRAY @>: tags.any(value).
            # Document.tags is annotated list[str] (SQLModel ergonomics); access the
            # underlying SQLAlchemy column instrument for query construction.
            tags_col = Document.__table__.c.tags  # ty: ignore[unresolved-attribute]
            stmt = stmt.where(tags_col.any(tag_norm))
        total_result = await self._session.exec(select(func.count()).select_from(stmt.subquery()))
        total = total_result.one()
        page_result = await self._session.exec(stmt.offset(offset).limit(limit))
        rows = list(page_result.all())
        return rows, total

    async def update_status(
        self,
        document_id: UUID,
        status: DocumentStatus,
        error_message: str | None = None,
    ) -> Document:
        doc = await self.get_by_id(document_id)
        if doc is None:
            raise DocumentNotFoundError(f'no document with id {document_id}')
        doc.status = status
        doc.error_message = error_message
        self._session.add(doc)
        await self._session.commit()
        await self._session.refresh(doc)
        return doc

    async def update_chunk_count(
        self,
        document_id: UUID,
        chunk_count: int,
    ) -> Document:
        doc = await self.get_by_id(document_id)
        if doc is None:
            raise DocumentNotFoundError(f'no document with id {document_id}')
        doc.chunk_count = chunk_count
        self._session.add(doc)
        await self._session.commit()
        await self._session.refresh(doc)
        return doc

    async def delete(self, document_id: UUID) -> None:
        doc = await self.get_by_id(document_id)
        if doc is None:
            raise DocumentNotFoundError(f'no document with id {document_id}')
        await self._session.delete(doc)
        await self._session.commit()

    async def list_by_status(
        self,
        status: DocumentStatus,
        offset: int = 0,
        limit: int = 1000,
    ) -> tuple[list[Document], int]:
        stmt = select(Document).where(Document.status == status)
        total_result = await self._session.exec(select(func.count()).select_from(stmt.subquery()))
        total = total_result.one()
        page_result = await self._session.exec(stmt.offset(offset).limit(limit))
        rows = list(page_result.all())
        return rows, total

    async def list_all_tags(self) -> list[str]:
        rows, _ = await self.list_documents(limit=10_000)
        seen: set[str] = set()
        for doc in rows:
            seen.update(doc.tags)
        return sorted(seen)
