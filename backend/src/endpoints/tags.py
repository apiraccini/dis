from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from src.core.dependencies import get_request_document_repo
from src.repositories.protocols import DocumentRepository
from src.schemas import TagsResponse
from src.services.tags import list_tags as list_tags_service

router = APIRouter(prefix='/api', tags=['tags'])

DocumentRepoDep = Annotated[DocumentRepository, Depends(get_request_document_repo)]


@router.get('/tags', response_model=TagsResponse)
async def list_tags(docs: DocumentRepoDep) -> TagsResponse:
    """Return all unique, sorted tags across all documents."""
    return TagsResponse(tags=await list_tags_service(docs))
