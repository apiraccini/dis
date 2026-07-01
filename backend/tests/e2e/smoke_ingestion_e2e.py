"""End-to-end ingestion smoke (task 7.2): real ingest() against compose db + qdrant.

Run:

    POSTGRES_HOST=localhost QDRANT_URL=http://localhost:6333 \
        uv run python -m tests.e2e.smoke_ingestion_e2e

Feeds a tiny born-digital PDF through the real MarkItDownParser → SemchunkChunker
→ OpenRouterEmbedder (Qwen3-embedding-8b) + FastEmbedSparseEmbedder (BM25) →
QdrantVectorStore + SqlModelDocumentRepository, then verifies the Document is
`ready`, chunk_count > 0, and a hybrid search returns the ingested chunk.
"""

from __future__ import annotations

import asyncio
import os
import sys

from openai import AsyncOpenAI
from qdrant_client import AsyncQdrantClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.config import settings
from src.repositories.document_repo import SqlModelDocumentRepository
from src.services.adapters.fastembed_sparse import FastEmbedSparseEmbedder
from src.services.adapters.markitdown_parser import MarkItDownParser
from src.services.adapters.openrouter_embedder import OpenRouterEmbedder
from src.services.adapters.qdrant_vector_store import QdrantVectorStore
from src.services.adapters.semchunk_chunker import SemchunkChunker
from src.services.ingestion import IngestionService


def _make_pdf(text: str) -> bytes:
    """Minimal born-digital PDF with a single text-layer line."""
    content_stream = f'BT /F1 24 Tf 72 700 Td ({text}) Tj ET\n'.encode()
    objects = [
        b'<< /Type /Catalog /Pages 2 0 R >>',
        b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
        b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] '
        b'/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',
        b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
        b'<< /Length '
        + str(len(content_stream)).encode()
        + b' >>\nstream\n'
        + content_stream
        + b'endstream',
    ]
    pdf = b'%PDF-1.4\n'
    offsets: list[int] = []
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf += f'{i} 0 obj\n'.encode() + obj + b'\nendobj\n'
    xref_pos = len(pdf)
    pdf += b'xref\n0 ' + str(len(objects) + 1).encode() + b'\n'
    pdf += b'0000000000 65535 f \n'
    for off in offsets:
        pdf += f'{off:010d} 00000 n \n'.encode()
    pdf += (
        b'trailer\n<< /Size '
        + str(len(objects) + 1).encode()
        + b' /Root 1 0 R >>\nstartxref\n'
        + str(xref_pos).encode()
        + b'\n%%EOF\n'
    )
    return pdf


COLLECTION = 'documents_ingest_smoke'


async def main() -> None:
    # Override settings for host-local run (compose uses container hostnames).
    settings.postgres_host = os.environ.get('POSTGRES_HOST', 'localhost')
    settings.qdrant_url = os.environ.get('QDRANT_URL', 'http://localhost:6333')
    settings.qdrant_collection = COLLECTION

    # DB setup (mirrors src/db.py but pointed at localhost).
    engine = create_async_engine(settings.database_url, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    sessionmaker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    qdrant = AsyncQdrantClient(url=settings.qdrant_url)
    vectors = QdrantVectorStore(client=qdrant, collection=COLLECTION)
    if await qdrant.collection_exists(COLLECTION):
        await qdrant.delete_collection(COLLECTION)
    await vectors.provision(settings.embedding_dimensions)

    parser = MarkItDownParser()
    chunker = SemchunkChunker(
        chunk_size=settings.chunk_size_tokens, overlap=settings.chunk_overlap_tokens
    )
    embedder = OpenRouterEmbedder(
        model=settings.embedding_model,
        dimensions=settings.embedding_dimensions,
        batch_size=settings.embedding_batch_size,
        input_type=settings.embedding_input_type_document,
        base_url=settings.embedding_base_url,
        api_key=settings.openrouter_api_key,
        client=AsyncOpenAI(
            base_url=settings.embedding_base_url, api_key=settings.openrouter_api_key
        ),
    )
    sparse_embedder = FastEmbedSparseEmbedder()

    async with sessionmaker() as session:
        documents = SqlModelDocumentRepository(session)
        service = IngestionService(
            parser=parser,
            chunker=chunker,
            embedder=embedder,
            sparse_embedder=sparse_embedder,
            documents=documents,
            vectors=vectors,
        )

        pdf = _make_pdf('Quarterly revenue grew 15 percent year over year')
        print('  ingesting born-digital PDF...')
        doc = await service.ingest(content=pdf, filename='q3-report.pdf', tags=['finance'])

        # 1. Document is ready with chunk_count > 0.
        assert doc.status.value == 'ready', f'status={doc.status}'
        assert doc.chunk_count > 0, f'chunk_count={doc.chunk_count}'
        print(
            f'  [ok] document ready: id={doc.id} '
            f'chunks={doc.chunk_count} hash={doc.content_hash[:8]}'
        )

        # 2. Re-ingest (dedup) returns the same document, no new chunks.
        before = (await qdrant.count(COLLECTION, exact=True)).count
        doc2 = await service.ingest(content=pdf, filename='dup.pdf', tags=['finance'])
        after = (await qdrant.count(COLLECTION, exact=True)).count
        assert doc2.id == doc.id, 'dedup should return existing document'
        assert before == after, f'dedup should not add chunks ({before} -> {after})'
        print(f'  [ok] dedup: same id, vector count unchanged ({after})')

    # 3. Semantic search via the query-input-type embedder finds the chunk.
    query_embedder = OpenRouterEmbedder(
        model=settings.embedding_model,
        dimensions=settings.embedding_dimensions,
        batch_size=settings.embedding_batch_size,
        input_type=settings.embedding_input_type_query,
        base_url=settings.embedding_base_url,
        api_key=settings.openrouter_api_key,
        client=AsyncOpenAI(
            base_url=settings.embedding_base_url, api_key=settings.openrouter_api_key
        ),
    )
    qv = await query_embedder.embed(['year over year revenue growth'])
    qsv = await sparse_embedder.embed(['year over year revenue growth'])
    hits = await vectors.search(qv[0], qsv[0], top_k=5, tags=['finance'])
    assert hits, 'expected at least one search hit'
    assert any('revenue' in h.text.lower() for h in hits), (
        f'no revenue hit: {[h.text for h in hits]}'
    )
    print(f'  [ok] hybrid search: {len(hits)} hit(s), top score={hits[0].score:.4f}')
    print(f'       top hit: {hits[0].text[:60]!r} (chunk {hits[0].chunk_index})')

    # 4. Filter pushdown by document_id.
    hits_doc = await vectors.search(qv[0], qsv[0], top_k=5, document_ids=[doc.id])
    assert hits_doc, 'document_id filter should match the ingested doc'
    print(f'  [ok] document_id filter: {len(hits_doc)} hit(s)')

    await qdrant.delete_collection(COLLECTION)
    await engine.dispose()
    print('\nEND-TO-END INGESTION SMOKE PASSED')


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except AssertionError as e:
        print(f'E2E SMOKE FAILED: {e}', file=sys.stderr)
        raise SystemExit(1) from e
