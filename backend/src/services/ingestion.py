from __future__ import annotations

import contextlib
import hashlib
import logging
from uuid import UUID

from src.models.document import Document, DocumentStatus, normalize_tags
from src.repositories.protocols import ChunkPayload, DocumentRepository, VectorStore
from src.services.protocols import Chunker, Embedder, Parser

logger = logging.getLogger(__name__)

__all__ = ['IngestionService', 'cleanup_zombies']


class IngestionService:
    def __init__(
        self,
        *,
        parser: Parser,
        chunker: Chunker,
        embedder: Embedder,
        documents: DocumentRepository,
        vectors: VectorStore,
    ) -> None:
        self._parser = parser
        self._chunker = chunker
        self._embedder = embedder
        self._documents = documents
        self._vectors = vectors

    async def prepare(self, *, content: bytes, filename: str, tags: list[str]) -> Document:
        content_hash = hashlib.sha256(content).hexdigest()

        existing = await self._documents.get_by_hash(content_hash)
        if existing is not None:
            return existing

        parsed_text = await self._parser.parse(content, filename)
        document = Document(
            filename=filename,
            content_type=None,
            size_bytes=len(content),
            content_hash=content_hash,
            parsed_text=parsed_text,
            tags=normalize_tags(tags),
            status=DocumentStatus.processing,
        )
        return await self._documents.create(document)

    async def finalize(self, document_id: UUID) -> Document:
        document = await self._documents.get_by_id(document_id)
        if document is None:
            from src.core.errors import DocumentNotFoundError

            raise DocumentNotFoundError(f'no document with id {document_id}')

        chunks = self._chunker.chunk(document.parsed_text)
        vectors = await self._embedder.embed(chunks)
        records = [
            ChunkPayload(
                document_id=document.id,
                document_name=document.filename,
                tags=list(document.tags),
                chunk_index=i,
                text=chunk,
            )
            for i, chunk in enumerate(chunks)
        ]
        await self._vectors.upsert(document.id, records, vectors)
        await self._documents.update_chunk_count(document_id, len(chunks))
        return await self._documents.update_status(document_id, DocumentStatus.ready)

    async def finalize_safe(self, document_id: UUID) -> None:
        """Run finalize in a background-task-safe way.

        Never propagates exceptions — catches and sets failed status instead.
        """
        try:
            await self.finalize(document_id)
        except Exception as exc:
            with contextlib.suppress(Exception):
                await self._documents.update_status(
                    document_id,
                    DocumentStatus.failed,
                    error_message=str(exc),
                )

    async def delete_document(self, document_id: UUID) -> None:
        await self._documents.delete(document_id)
        await self._vectors.delete_by_document(document_id)

    async def ingest(self, *, content: bytes, filename: str, tags: list[str]) -> Document:
        prepared = await self.prepare(content=content, filename=filename, tags=tags)
        if prepared.status == DocumentStatus.ready:
            return prepared
        return await self.finalize(prepared.id)


async def cleanup_zombies(documents: DocumentRepository) -> None:
    """Mark any documents stuck in 'processing' as 'failed'.

    Called on application startup to clean up documents that were being
    processed when the server was killed.
    """
    rows, total = await documents.list_by_status(DocumentStatus.processing, limit=5000)
    if total == 0:
        return
    logger.warning('Cleaning up %d zombie documents (status=processing)', total)
    for doc in rows:
        msg = 'Application restart while processing'
        await documents.update_status(doc.id, DocumentStatus.failed, error_message=msg)
