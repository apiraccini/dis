from __future__ import annotations

import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import Index
from sqlalchemy.dialects.postgresql import ARRAY, TIMESTAMP
from sqlmodel import Column, Field, SQLModel, String

__all__ = ['Document', 'DocumentStatus', 'normalize_tags']


class DocumentStatus(enum.StrEnum):
    pending = 'pending'
    processing = 'processing'
    ready = 'ready'
    failed = 'failed'


def normalize_tags(tags: list[str] | None) -> list[str]:
    """Normalize tag strings: lowercase, strip, drop empties, dedupe.

    Order of first occurrence is preserved. Returns a new list; the input list
    is not mutated.
    """
    if not tags:
        return []
    seen: set[str] = set()
    result: list[str] = []
    for tag in tags:
        normalized = tag.strip().lower()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


class Document(SQLModel, table=True):
    __tablename__ = 'document'
    # GIN index on the tags array supports array-containment filters (list-by-tag).
    __table_args__ = (Index('ix_document_tags_gin', 'tags', postgresql_using='gin'),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    filename: str
    content_type: str | None = None
    size_bytes: int = 0
    # SHA-256 hex of the parsed text — the dedup key. Unique constraint enforced at the DB.
    content_hash: str = Field(unique=True)
    parsed_text: str
    tags: list[str] = Field(
        default_factory=list,
        sa_column=Column(ARRAY(String), nullable=False, server_default='{}'),
    )
    status: DocumentStatus = Field(default=DocumentStatus.pending)
    error_message: str | None = None
    chunk_count: int = Field(default=0)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False),
    )
