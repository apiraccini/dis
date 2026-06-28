from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.models.document import DocumentStatus


class DocumentResponse(BaseModel):
    """Document fields returned in list responses (omits parsed_text)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    content_type: str | None = None
    size_bytes: int = 0
    content_hash: str
    tags: list[str]
    status: DocumentStatus
    error_message: str | None = None
    chunk_count: int = 0
    created_at: datetime
    updated_at: datetime


class DocumentDetailResponse(DocumentResponse):
    """Full document including parsed_text (used for get-by-id and upload responses)."""

    parsed_text: str


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int


class TagsResponse(BaseModel):
    tags: list[str]
