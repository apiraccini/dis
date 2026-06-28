from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastmcp.utilities.lifespan import combine_lifespans

from src.core.config import settings
from src.db import init_db
from src.mcp_server import mcp_app


@asynccontextmanager
async def db_lifespan(_app: FastAPI) -> AsyncIterator[None]:
    await init_db()
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


# REST routers will be included here as endpoints are built:
# from src.endpoints import documents
# app.include_router(documents.router, prefix="/api")
app.mount('/mcp', mcp_app)
