"""Live integration smoke for the Qdrant VectorStore (task 7.1).

Run against the compose `qdrant` service. Not part of the unit suite — invoke
explicitly:

    POSTGRES_HOST=localhost QDRANT_URL=http://localhost:6333 \
        uv run python -m tests.smoke_qdrant_live

Asserts: ensure_collection (idempotent) → upsert two chunks → search returns
ranked hits → filter by tag and document_id → delete_by_document → re-search
empty. Also verifies the payload indexes were created.
"""

from __future__ import annotations

import asyncio
import os
import sys
from uuid import UUID

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qm

from src.repositories.protocols import ChunkRecord
from src.services.adapters.qdrant_vector_store import QdrantVectorStore

DOC_ID = UUID('22222222-2222-2222-2222-222222222222')
COLLECTION = 'documents_smoke'


async def main() -> None:
    url = os.environ.get('QDRANT_URL', 'http://localhost:6333')
    client = AsyncQdrantClient(url=url)
    store = QdrantVectorStore(client=client, collection=COLLECTION)

    # Fresh start: drop if it exists from a prior run.
    if await client.collection_exists(COLLECTION):
        await client.delete_collection(COLLECTION)

    # 1. provision creates collection + payload indexes.
    await store.provision(dim=1536)
    assert await client.collection_exists(COLLECTION), 'collection not created'
    info = await client.get_collection(COLLECTION)
    vectors_cfg = info.config.params.vectors
    assert not isinstance(vectors_cfg, dict)
    assert vectors_cfg is not None
    assert vectors_cfg.size == 1536
    assert vectors_cfg.distance == qm.Distance.COSINE
    indexed = set((info.payload_schema or {}).keys())
    assert {'document_id', 'tags'} <= indexed, f'missing payload indexes: {indexed}'
    print(f'  [ok] provision: collection + indexes {sorted(indexed & {"document_id", "tags"})}')

    # 2. idempotent re-provision is a no-op (no error, collection still there).
    await store.provision(dim=1536)
    print('  [ok] re-provision idempotent')

    # 3. upsert two chunks.
    chunks = [
        ChunkRecord(DOC_ID, 'report.pdf', ['compliance', 'finance'], 0, 'revenue grew 10%'),
        ChunkRecord(DOC_ID, 'report.pdf', ['compliance', 'finance'], 1, 'audit passed cleanly'),
    ]
    vectors = [[0.9, 0.1, 0.0] + [0.0] * 1533, [0.1, 0.9, 0.0] + [0.0] * 1533]
    await store.upsert(DOC_ID, chunks, vectors)
    print('  [ok] upsert 2 chunks')

    # 4. re-upsert replaces (atomic) — count stays 2, not 4.
    await store.upsert(DOC_ID, chunks, vectors)
    count_after = (await client.count(COLLECTION, exact=True)).count
    assert count_after == 2, f'expected 2 after re-upsert, got {count_after}'
    print(f'  [ok] re-upsert atomic replace (count={count_after})')

    # 5. search returns ranked hits; the closer vector wins.
    hits = await store.search([0.95, 0.05, 0.0] + [0.0] * 1533, top_k=5)
    assert len(hits) == 2, f'expected 2 hits, got {len(hits)}'
    assert hits[0].score >= hits[1].score, 'hits not ranked by descending score'
    assert hits[0].chunk_index == 0, 'nearest vector should be chunk 0'
    assert hits[0].document_name == 'report.pdf'
    assert hits[0].tags == ['compliance', 'finance']
    print(f'  [ok] search ranked (top score={hits[0].score:.4f})')

    # 6. filter by tag narrows to matching chunks.
    hits_tag = await store.search([0.95, 0.05, 0.0] + [0.0] * 1533, top_k=5, tags=['compliance'])
    assert len(hits_tag) == 2, f'tag filter should match both, got {len(hits_tag)}'
    hits_no = await store.search([0.95, 0.05, 0.0] + [0.0] * 1533, top_k=5, tags=['nonexistent'])
    assert hits_no == [], 'nonexistent tag should return nothing'
    print('  [ok] tag filter pushdown (match + no-match)')

    # 7. filter by document_id.
    hits_doc = await store.search([0.95, 0.05, 0.0] + [0.0] * 1533, top_k=5, document_ids=[DOC_ID])
    assert len(hits_doc) == 2
    hits_other = await store.search(
        [0.95, 0.05, 0.0] + [0.0] * 1533,
        top_k=5,
        document_ids=[UUID('33333333-3333-3333-3333-333333333333')],
    )
    assert hits_other == [], 'other document_id should return nothing'
    print('  [ok] document_id filter pushdown (match + no-match)')

    # 8. delete_by_document clears the chunks; re-search is empty.
    await store.delete_by_document(DOC_ID)
    assert (await client.count(COLLECTION, exact=True)).count == 0
    assert await store.search([0.95, 0.05, 0.0] + [0.0] * 1533, top_k=5) == []
    # delete is a no-op when already empty.
    await store.delete_by_document(DOC_ID)
    print('  [ok] delete_by_document (clears + idempotent no-op)')

    # Cleanup.
    await client.delete_collection(COLLECTION)
    print('\nALL QDRANT SMOKE CHECKS PASSED')


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except AssertionError as e:
        print(f'SMOKE FAILED: {e}', file=sys.stderr)
        raise SystemExit(1) from e
