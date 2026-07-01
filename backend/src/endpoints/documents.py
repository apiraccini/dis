from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Form,
    HTTPException,
    Response,
    UploadFile,
    status,
)

from src.core.dependencies import get_document_repository, get_ingestion_service
from src.core.errors import DocumentNotFoundError, DuplicateDocumentError, ParseError
from src.models.document import Document
from src.repositories.protocols import DocumentRepository
from src.schemas import (
    DocumentDetailResponse,
    DocumentListResponse,
    DocumentResponse,
)
from src.services.ingestion import IngestionService

router = APIRouter(prefix='/api/documents', tags=['documents'])

IngestionServiceDep = Annotated[IngestionService, Depends(get_ingestion_service)]
DocumentRepoDep = Annotated[DocumentRepository, Depends(get_document_repository)]


def _split_tags(tags_str: str | None) -> list[str]:
    if not tags_str or not tags_str.strip():
        return []
    return tags_str.split(',')


def _to_detail(doc: Document) -> DocumentDetailResponse:
    return DocumentDetailResponse.model_validate(doc, from_attributes=True)


def _to_summary(doc: Document) -> DocumentResponse:
    return DocumentResponse.model_validate(doc, from_attributes=True)


@router.post('/upload', response_model=DocumentDetailResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile,
    service: IngestionServiceDep,
    tags: str = Form(''),
) -> Response:
    """Upload a file for ingestion.

    Returns 202 + processing document on upload (background finalize).
    Raises 409 if the content is a duplicate of an existing document.
    """
    content = await file.read()
    tags_list = _split_tags(tags)

    try:
        prepared = await service.prepare(
            content=content,
            filename=file.filename or 'unnamed',
            tags=tags_list,
            content_type=file.content_type,
        )
    except ParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from None
    except DuplicateDocumentError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from None

    background_tasks.add_task(service.finalize_safe, prepared.id)
    return Response(
        content=_to_detail(prepared).model_dump_json(),
        media_type='application/json',
        status_code=status.HTTP_202_ACCEPTED,
    )


@router.get('', response_model=DocumentListResponse)
async def list_documents(
    docs: DocumentRepoDep,
    offset: int = 0,
    limit: int = 100,
    tag: str | None = None,
) -> DocumentListResponse:
    rows, total = await docs.list_documents(offset=offset, limit=limit, tag=tag)
    items = [_to_summary(d) for d in rows]
    return DocumentListResponse(items=items, total=total)


@router.get('/{document_id}', response_model=DocumentDetailResponse)
async def get_document(
    document_id: str,
    docs: DocumentRepoDep,
) -> DocumentDetailResponse:
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Document not found',
        ) from None
    doc = await docs.get_by_id(doc_uuid)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Document not found')
    return _to_detail(doc)


@router.delete('/{document_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    service: IngestionServiceDep,
) -> None:
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Document not found',
        ) from None
    try:
        await service.delete_document(doc_uuid)
    except DocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Document not found',
        ) from None
