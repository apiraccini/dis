from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from src.core.dependencies import get_document_repository
from src.repositories.protocols import DocumentRepository
from src.schemas import TagsResponse

router = APIRouter(prefix='/api', tags=['tags'])

DocumentRepoDep = Annotated[DocumentRepository | None, Depends(get_document_repository)]


@router.get('/tags', response_model=TagsResponse)
async def list_tags(docs: DocumentRepoDep = None) -> TagsResponse:
    """Return all unique, sorted tags across all documents."""
    rows, _total = await docs.list_documents(limit=10_000)  # ty: ignore[unresolved-attribute]
    all_tags: set[str] = set()
    for doc in rows:
        all_tags.update(doc.tags)
    return TagsResponse(tags=sorted(all_tags))
