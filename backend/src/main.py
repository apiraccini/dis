from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastmcp.utilities.lifespan import combine_lifespans

from src.core.config import settings
from src.core.dependencies import set_adapters
from src.db import async_session, init_db
from src.endpoints import documents, tags
from src.mcp_server import mcp_app
from src.repositories.document_repo import SqlModelDocumentRepository
from src.services.factory import build_adapters
from src.services.ingestion import cleanup_zombies


@asynccontextmanager
async def db_lifespan(_app: FastAPI) -> AsyncIterator[None]:
    await init_db()
    # Build the singleton ingestion adapters and provision the Qdrant
    # collection (idempotent) so filtered HNSW + payload indexes are ready.
    adapters = build_adapters(settings)
    # Provision to the embedder's actual output width, not config, so they can't diverge.
    await adapters.vectors.provision(adapters.embedder.dimension)
    set_adapters(adapters)  # shared singleton for REST + MCP tools

    # Clean up zombie documents left in processing state by a prior crash.
    async with async_session() as session:
        repo = SqlModelDocumentRepository(session)
        await cleanup_zombies(repo)
        await session.commit()

    yield


# Compose DB init + MCP session-manager lifespan (combine enters in order, exits in reverse).
app = FastAPI(
    title='Document Intelligence Server',
    version='0.1.0',
    lifespan=combine_lifespans(db_lifespan, mcp_app.lifespan),
)

# CORS applies to the REST API only; the mounted MCP app is a separate sub-app.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.get('/health')
async def health() -> dict[str, str]:
    return {'status': 'ok'}


app.include_router(documents.router)
app.include_router(tags.router)

app.mount('/mcp', mcp_app)
