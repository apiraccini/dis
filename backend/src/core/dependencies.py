from __future__ import annotations

from collections.abc import AsyncGenerator, AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db import async_session, get_session
from src.repositories.document_repo import SqlModelDocumentRepository
from src.repositories.protocols import DocumentRepository
from src.services.factory import Adapters, build_ingestion_service
from src.services.ingestion import IngestionService

# Thin alias so endpoints import dependency from core.dependencies.
get_db = get_session

# Module-level singleton (not app.state) so both FastAPI endpoints and FastMCP tools —
# two separate DI systems — can share the same instance without threading app state
# through both.
_adapters: Adapters | None = None


def set_adapters(adapters: Adapters) -> None:
    global _adapters
    _adapters = adapters


def get_adapters() -> Adapters:
    if _adapters is None:
        raise RuntimeError('adapters not initialized')
    return _adapters


async def get_ingestion_service(
    session: Annotated[AsyncSession, Depends(get_db)],
    adapters: Annotated[Adapters, Depends(get_adapters)],
) -> AsyncGenerator[IngestionService, None]:
    yield build_ingestion_service(session, adapters)


FinalizeFn = Callable[[UUID], Awaitable[None]]


def get_finalizer(
    adapters: Annotated[Adapters, Depends(get_adapters)],
) -> FinalizeFn:
    """Return a background-task-safe finalize callable.

    FastAPI tears down yield-dependencies before background tasks run, so the
    request-scoped session must not be reused there; the callable opens its own.
    """

    async def _finalize(document_id: UUID) -> None:
        async with async_session() as session:
            await build_ingestion_service(session, adapters).finalize_safe(document_id)

    return _finalize


async def get_request_document_repo(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> AsyncGenerator[DocumentRepository, None]:
    yield SqlModelDocumentRepository(session)


@asynccontextmanager
async def get_document_repo() -> AsyncIterator[DocumentRepository]:
    async with async_session() as session:
        yield SqlModelDocumentRepository(session)


__all__ = [
    'FinalizeFn',
    'get_adapters',
    'get_db',
    'get_document_repo',
    'get_finalizer',
    'get_ingestion_service',
    'get_request_document_repo',
    'get_session',
    'set_adapters',
]
