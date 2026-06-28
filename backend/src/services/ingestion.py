from __future__ import annotations

import hashlib
from uuid import UUID

from src.models.document import Document, DocumentStatus, normalize_tags
from src.repositories.protocols import ChunkRecord, DocumentRepository, VectorStore
from src.services.protocols import Chunker, Embedder, Parser

__all__ = ['IngestionService']


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
        parsed_text = await self._parser.parse(content, filename)
        content_hash = hashlib.sha256(parsed_text.encode()).hexdigest()

        existing = await self._documents.get_by_hash(content_hash)
        if existing is not None:
            return existing

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

        try:
            chunks = self._chunker.chunk(document.parsed_text)
            vectors = await self._embedder.embed(chunks)
            records = [
                ChunkRecord(
                    document_id=document.id,
                    document_name=document.filename,
                    tags=list(document.tags),
                    chunk_index=i,
                    text=chunk,
                )
                for i, chunk in enumerate(chunks)
            ]
            await self._vectors.upsert(document.id, records, vectors)
        except Exception as exc:
            await self._documents.update_status(
                document_id, DocumentStatus.failed, error_message=str(exc)
            )
            raise
        await self._documents.update_chunk_count(document_id, len(chunks))
        return await self._documents.update_status(document_id, DocumentStatus.ready)

    async def ingest(self, *, content: bytes, filename: str, tags: list[str]) -> Document:
        prepared = await self.prepare(content=content, filename=filename, tags=tags)
        if prepared.status == DocumentStatus.ready:
            return prepared
        return await self.finalize(prepared.id)
