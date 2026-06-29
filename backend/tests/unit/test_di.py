from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.dependencies import get_adapters, get_document_repo, set_adapters
from src.services.factory import Adapters


def _make_adapters() -> Adapters:
    return Adapters(
        parser=MagicMock(),
        chunker=MagicMock(),
        embedder=MagicMock(),
        query_embedder=MagicMock(),
        vectors=MagicMock(),
    )


def test_set_adapters_stores_adapters() -> None:
    adapters = _make_adapters()

    import src.core.dependencies as deps

    deps._adapters = None

    set_adapters(adapters)

    assert deps._adapters is adapters


def test_get_adapters_returns_set_adapters() -> None:
    adapters = _make_adapters()

    import src.core.dependencies as deps

    deps._adapters = adapters

    result = get_adapters()

    assert result is adapters


def test_get_adapters_raises_when_not_initialized() -> None:
    import src.core.dependencies as deps

    deps._adapters = None

    with pytest.raises(RuntimeError, match='adapters not initialized'):
        get_adapters()


@pytest.mark.asyncio
async def test_get_document_repo_yields_repository() -> None:
    """get_document_repo creates an AsyncSession and yields a SqlModelDocumentRepository."""
    mock_session = AsyncMock()
    mock_session.__aenter__.return_value = mock_session

    with patch('src.core.dependencies.async_session') as mock_async_session:
        mock_async_session.return_value = mock_session
        with patch('src.core.dependencies.SqlModelDocumentRepository') as mock_repo_cls:
            mock_repo = MagicMock()
            mock_repo_cls.return_value = mock_repo

            async with get_document_repo() as repo:
                assert repo is mock_repo

            mock_repo_cls.assert_called_once_with(mock_session)
