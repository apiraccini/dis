from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from src.db import get_session, init_db


@pytest.mark.asyncio
async def test_get_session_yields_session() -> None:
    """get_session creates an async_session and yields it."""
    mock_session = AsyncMock()
    mock_session.__aenter__.return_value = mock_session

    with patch('src.db.async_session') as mock_async_session:
        mock_async_session.return_value = mock_session

        async for session in get_session():
            assert session is mock_session


@pytest.mark.asyncio
async def test_get_session_closes_on_exit() -> None:
    """Session context manager is entered and exited properly."""
    mock_session = AsyncMock()
    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_session
    mock_context.__aexit__.return_value = None

    with patch('src.db.async_session', return_value=mock_context):
        async for _ in get_session():
            pass

    # __aexit__ should have been called when the generator finishes
    mock_context.__aexit__.assert_awaited_once()


@pytest.mark.asyncio
async def test_init_db_creates_tables() -> None:
    """init_db imports models and calls create_all."""
    mock_connection = AsyncMock()
    mock_connection.__aenter__.return_value = mock_connection

    with (
        patch('src.db.engine') as mock_engine,
        patch('src.db.SQLModel') as mock_sqlmodel,
    ):
        mock_engine.begin.return_value = mock_connection

        await init_db()

    # engine.begin() was called
    mock_engine.begin.assert_called_once()
    # run_sync was called with create_all
    mock_connection.run_sync.assert_awaited_once_with(mock_sqlmodel.metadata.create_all)
