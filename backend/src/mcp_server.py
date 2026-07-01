from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastmcp import FastMCP
from fastmcp.dependencies import Depends
from fastmcp.exceptions import ToolError
from pydantic import BaseModel, Field

from src.core.config import settings
from src.core.dependencies import get_adapters, get_document_repo
from src.core.security import build_mcp_auth
from src.repositories.protocols import DocumentRepository, SearchHit
from src.services.factory import Adapters
from src.services.tags import list_tags as list_tags_service

mcp = FastMCP('DIS Knowledge Base', auth=build_mcp_auth())

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

    def to_text(self) -> str:
        if not self.documents:
            return 'No documents found.'
        lines = [f'{len(self.documents)} document(s) (total {self.total}):']
        for d in self.documents:
            tags = ', '.join(d.tags) if d.tags else 'no tags'
            lines.append(
                f'- {d.filename} [{d.id}] — {tags} — {d.status}, '
                f'{d.chunk_count} chunks, uploaded {d.created_at}'
            )
        return '\n'.join(lines)


class ListTagsResult(BaseModel):
    tags: list[str]

    def to_text(self) -> str:
        return ', '.join(self.tags) if self.tags else 'No tags found.'


class SearchHitResult(BaseModel):
    document_id: str
    document_name: str
    tags: list[str]
    chunk_index: int
    text: str
    score: float


class SearchResult(BaseModel):
    hits: list[SearchHitResult]

    def to_text(self) -> str:
        if not self.hits:
            return 'No matching chunks found.'
        lines = [f'{len(self.hits)} hit(s):']
        for i, h in enumerate(self.hits, start=1):
            tags = ', '.join(h.tags) if h.tags else 'no tags'
            lines.append(
                f'[{i}] {h.document_name} (id={h.document_id}, chunk={h.chunk_index}, '
                f'score={h.score:.3f}) — tags: {tags}\n{h.text}'
            )
        return '\n\n'.join(lines)


# ── Tools ───────────────────────────────────────────────────────────────


@mcp.tool
async def list_documents(
    offset: Annotated[int, Field(description='Number of documents to skip, for pagination.')] = 0,
    limit: Annotated[
        int,
        Field(
            description=(
                f'Maximum number of documents to return (hard cap: {settings.max_page_size}).'
            )
        ),
    ] = 100,
    tag: Annotated[
        str | None,
        Field(
            description='Only include documents carrying this exact tag. Omit for all documents.'
        ),
    ] = None,
    repo: DocumentRepository = Depends(get_document_repo),  # noqa: B008
):
    """List known documents and their metadata (filename, tags, status, chunk count).

    Use this to discover which documents exist and their IDs/tags before calling
    `search` with a `document_ids` or `tags` filter. Does not return document content —
    use `search` for that.
    """
    rows, total = await repo.list_documents(offset=offset, limit=limit, tag=tag)
    result = ListDocumentsResult(
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
    return result.to_text()


@mcp.tool
async def list_tags(
    repo: DocumentRepository = Depends(get_document_repo),  # noqa: B008
):
    """Return all unique tags currently assigned to at least one document, sorted alphabetically.

    Use this to discover valid tag values before calling `search` with a `tags` filter.
    """
    result = ListTagsResult(tags=await list_tags_service(repo))
    return result.to_text()


async def _search(
    query: str,
    top_k: int,
    adapters: Adapters,
    tags: list[str] | None = None,
    document_ids: list[str] | None = None,
) -> SearchResult:
    top_k = min(top_k, settings.max_search_top_k)
    ids: list[UUID] | None = None
    if document_ids:
        try:
            ids = [UUID(did) for did in document_ids]
        except ValueError as exc:
            raise ToolError(f'invalid document id: {exc}') from exc

    [vector] = await adapters.query_embedder.embed([query])
    [sparse_vector] = await adapters.sparse_embedder.embed([query])
    hits: list[SearchHit] = await adapters.vectors.search(
        query=vector,
        sparse_query=sparse_vector,
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
    query: Annotated[str, Field(description='Natural language search query.')],
    top_k: Annotated[
        int,
        Field(
            description=(
                f'Maximum number of chunks to return (hard cap: {settings.max_search_top_k}).'
            )
        ),
    ] = 5,
    tags: Annotated[
        list[str] | None,
        Field(
            description=(
                'Only search documents carrying at least one of these tags (OR semantics). '
                'Use `list_tags` to discover valid values. Omit to search all documents.'
            )
        ),
    ] = None,
    document_ids: Annotated[
        list[str] | None,
        Field(
            description=(
                'Only search within these specific document UUIDs (as returned by '
                '`list_documents`). Omit to search all documents. If combined with `tags`, '
                'only chunks matching both filters are returned.'
            )
        ),
    ] = None,
    adapters: Adapters = Depends(get_adapters),  # noqa: B008
):
    """Semantically search the knowledge base and return the most relevant chunks.

    This is the primary and default way to retrieve document content — use it for
    every query, whether unfiltered or narrowed by `tags` and/or `document_ids`. Each
    hit includes its source document, tags, and similarity score. Call `list_tags` or
    `list_documents` first if you need to discover valid filter values.
    """
    result = await _search(query, top_k, adapters, tags=tags, document_ids=document_ids)
    return result.to_text()


# search_by_tag and search_by_document are superseded by search's built-in `tags` and
# `document_ids` filters, which cover the same functionality without adding tool-choice
# ambiguity for the calling agent. Kept for reference, not registered.
#
# @mcp.tool
# async def search_by_tag(
#     query: str,
#     tags: list[str],
#     top_k: int = 5,
#     adapters: Adapters = Depends(get_adapters),
# ) -> SearchResult:
#     """Semantically search chunks filtered by tag(s)."""
#     return await _search(query, top_k, adapters, tags=tags)
#
#
# @mcp.tool
# async def search_by_document(
#     query: str,
#     document_ids: list[str],
#     top_k: int = 5,
#     adapters: Adapters = Depends(get_adapters),
# ) -> SearchResult:
#     """Semantically search chunks filtered by document ID(s)."""
#     return await _search(query, top_k, adapters, document_ids=document_ids)


__all__ = ['mcp', 'mcp_app']
