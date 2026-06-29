from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from src.db import async_session
from src.repositories.document_repo import SqlModelDocumentRepository
from src.repositories.protocols import DocumentRepository
from src.services.factory import Adapters

# Module-level adapters singleton, set once at startup.
_adapters: Adapters | None = None


def set_adapters(adapters: Adapters) -> None:
    global _adapters
    _adapters = adapters


def get_adapters() -> Adapters:
    if _adapters is None:
        raise RuntimeError('adapters not initialized — call set_adapters during startup')
    return _adapters


@asynccontextmanager
async def get_document_repo() -> AsyncIterator[DocumentRepository]:
    async with async_session() as session:
        yield SqlModelDocumentRepository(session)


__all__ = [
    'get_adapters',
    'get_document_repo',
    'set_adapters',
]
