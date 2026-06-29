from __future__ import annotations

from uuid import UUID

from fastmcp import FastMCP
from fastmcp.dependencies import Depends
from pydantic import BaseModel

from src.core.security import build_mcp_auth
from src.repositories.protocols import DocumentRepository, SearchHit
from src.services.di import get_adapters, get_document_repo
from src.services.factory import Adapters

mcp = FastMCP('DIS Knowledge Base', auth=build_mcp_auth())

# path="/" → endpoint is exactly /mcp when mounted at /mcp (default /mcp yields /mcp/mcp).
# stateless_http + json_response go on http_app(), NOT the FastMCP constructor
# (PrefectHQ/fastmcp#3618).
mcp_app = mcp.http_app(
    path='/',
    stateless_http=True,
    json_response=True,
)


# ── Tool output models ──────────────────────────────────────────────────


class DocumentSummary(BaseModel):
    id: str
    filename: str
    tags: list[str]
    status: str
    chunk_count: int
    created_at: str


class ListDocumentsResult(BaseModel):
    documents: list[DocumentSummary]
    total: int


class ListTagsResult(BaseModel):
    tags: list[str]


class SearchHitResult(BaseModel):
    document_id: str
    document_name: str
    tags: list[str]
    chunk_index: int
    text: str
    score: float


class SearchResult(BaseModel):
    hits: list[SearchHitResult]


# ── Tools ───────────────────────────────────────────────────────────────


@mcp.tool
async def list_documents(
    offset: int = 0,
    limit: int = 100,
    tag: str | None = None,
    repo: DocumentRepository = Depends(get_document_repo),  # noqa: B008
) -> ListDocumentsResult:
    """List documents with pagination and optional tag filter."""
    rows, total = await repo.list_documents(offset=offset, limit=min(limit, 500), tag=tag)
    return ListDocumentsResult(
        documents=[
            DocumentSummary(
                id=str(d.id),
                filename=d.filename,
                tags=list(d.tags),
                status=d.status.value,
                chunk_count=d.chunk_count,
                created_at=d.created_at.isoformat(),
            )
            for d in rows
        ],
        total=total,
    )


@mcp.tool
async def list_tags(
    repo: DocumentRepository = Depends(get_document_repo),  # noqa: B008
) -> ListTagsResult:
    """Return all unique tags sorted alphabetically."""
    rows, _ = await repo.list_documents(offset=0, limit=10000)
    seen: set[str] = set()
    for doc in rows:
        seen.update(doc.tags)
    return ListTagsResult(tags=sorted(seen))


async def _search(
    query: str,
    top_k: int,
    adapters: Adapters,
    tags: list[str] | None = None,
    document_ids: list[str] | None = None,
) -> SearchResult:
    top_k = min(top_k, 50)
    ids: list[UUID] | None = None
    if document_ids:
        ids = [UUID(did) for did in document_ids]

    [vector] = await adapters.query_embedder.embed([query])
    hits: list[SearchHit] = await adapters.vectors.search(
        query=vector,
        top_k=top_k,
        tags=tags,
        document_ids=ids,
    )
    return SearchResult(
        hits=[
            SearchHitResult(
                document_id=str(h.document_id),
                document_name=h.document_name,
                tags=h.tags,
                chunk_index=h.chunk_index,
                text=h.text,
                score=h.score,
            )
            for h in hits
        ]
    )


@mcp.tool
async def search(
    query: str,
    top_k: int = 5,
    tags: list[str] | None = None,
    document_ids: list[str] | None = None,
    adapters: Adapters = Depends(get_adapters),  # noqa: B008
) -> SearchResult:
    """Semantically search chunks with optional tag and document filters."""
    return await _search(query, top_k, adapters, tags=tags, document_ids=document_ids)


@mcp.tool
async def search_by_tag(
    query: str,
    tags: list[str],
    top_k: int = 5,
    adapters: Adapters = Depends(get_adapters),  # noqa: B008
) -> SearchResult:
    """Semantically search chunks filtered by tag(s)."""
    return await _search(query, top_k, adapters, tags=tags)


@mcp.tool
async def search_by_document(
    query: str,
    document_ids: list[str],
    top_k: int = 5,
    adapters: Adapters = Depends(get_adapters),  # noqa: B008
) -> SearchResult:
    """Semantically search chunks filtered by document ID(s)."""
    return await _search(query, top_k, adapters, document_ids=document_ids)


__all__ = ['mcp', 'mcp_app']
