from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Request
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db import get_session
from src.repositories.protocols import DocumentRepository
from src.services.factory import Adapters, build_ingestion_service
from src.services.ingestion import IngestionService

# Thin alias so endpoints import dependency from core.dependencies.
get_db = get_session


async def get_adapters(request: Request) -> Adapters:
    return request.app.state.adapters


async def get_ingestion_service(
    session: Annotated[AsyncSession, Depends(get_db)],
    adapters: Annotated[Adapters, Depends(get_adapters)],
) -> AsyncGenerator[IngestionService, None]:
    yield build_ingestion_service(session, adapters)


async def get_document_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> AsyncGenerator[DocumentRepository, None]:
    from src.repositories.document_repo import SqlModelDocumentRepository

    yield SqlModelDocumentRepository(session)


__all__ = [
    'get_adapters',
    'get_db',
    'get_document_repository',
    'get_ingestion_service',
    'get_session',
]
