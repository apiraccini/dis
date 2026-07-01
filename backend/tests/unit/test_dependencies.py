from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.dependencies import (
    get_ingestion_service,
    get_request_document_repo,
)
from src.services.factory import Adapters


@pytest.mark.asyncio
async def test_get_ingestion_service_yields_service() -> None:
    """get_ingestion_service builds and yields an IngestionService."""
    mock_session = AsyncMock()
    mock_adapters = MagicMock(spec=Adapters)

    with patch('src.core.dependencies.build_ingestion_service') as mock_build:
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        gen = get_ingestion_service(mock_session, mock_adapters)
        service = await gen.__anext__()

        assert service is mock_service
        mock_build.assert_called_once_with(mock_session, mock_adapters)


@pytest.mark.asyncio
async def test_get_request_document_repo_yields_repo() -> None:
    """get_request_document_repo yields a SqlModelDocumentRepository."""
    mock_session = AsyncMock()

    gen = get_request_document_repo(mock_session)
    repo = await gen.__anext__()

    from src.repositories.document_repo import SqlModelDocumentRepository

    assert isinstance(repo, SqlModelDocumentRepository)
    assert repo._session is mock_session
