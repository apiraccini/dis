from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from src.core.config import settings

engine = create_async_engine(settings.database_url, echo=False, future=True)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


async def init_db() -> None:
    # No Alembic: tables auto-created from SQLModel.metadata on startup.
    # Import model modules here so they register before create_all runs.
    from src import models  # noqa: F401  (registers Document on metadata)

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
