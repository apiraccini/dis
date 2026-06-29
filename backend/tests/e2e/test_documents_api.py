"""REST API e2e: drives the live server (real Postgres + Qdrant, fake embedder)
over HTTP through the full document lifecycle.

Run via `scripts/run_e2e.sh`, which brings up the deps, launches uvicorn with
USE_FAKE_EMBEDDER=true, and invokes `pytest -m e2e`. Base URL comes from
E2E_BASE_URL (default http://localhost:8000).
"""

from __future__ import annotations

import os
import time
import uuid
from collections.abc import Iterator

# httpx2 is Pydantic's maintained successor to httpx (the original stalled in 2024);
# Starlette's TestClient now prefers it. Aliased so the call sites read as plain httpx.
import httpx2 as httpx
import pytest

pytestmark = pytest.mark.e2e

BASE_URL = os.environ.get('E2E_BASE_URL', 'http://localhost:8000')


@pytest.fixture
def client() -> Iterator[httpx.Client]:
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as c:
        yield c


@pytest.fixture
def unique_doc() -> tuple[bytes, str, str]:
    """Per-test unique (content, filename, tag) so the test is independent of any
    documents left in the persistent DB volume by prior runs (dedup is by content hash)."""
    token = uuid.uuid4().hex
    content = f'# Quarterly Report {token}\n\nRevenue grew 15 percent year over year.\n'.encode()
    return content, f'q3-report-{token}.md', f'e2e-{token}'


def _upload(client: httpx.Client, *, content: bytes, filename: str, tags: str) -> httpx.Response:
    return client.post(
        '/api/documents/upload',
        files={'file': (filename, content, 'text/markdown')},
        data={'tags': tags},
    )


def _poll_until_terminal(client: httpx.Client, doc_id: str, *, timeout_s: float = 30.0) -> dict:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        resp = client.get(f'/api/documents/{doc_id}')
        resp.raise_for_status()
        body = resp.json()
        if body['status'] in ('ready', 'failed'):
            return body
        time.sleep(0.5)
    raise AssertionError(f'document {doc_id} did not reach a terminal status within {timeout_s}s')


def test_full_document_lifecycle(client: httpx.Client, unique_doc: tuple[bytes, str, str]) -> None:
    content, filename, tag = unique_doc

    # Upload → 202 + processing document with an id.
    resp = _upload(client, content=content, filename=filename, tags=f'{tag}, Quarterly')
    assert resp.status_code == 202, resp.text
    created = resp.json()
    doc_id = created['id']
    assert created['status'] == 'processing'
    assert created['tags'] == [tag, 'quarterly']

    # Background finalize completes → ready with chunks.
    ready = _poll_until_terminal(client, doc_id)
    assert ready['status'] == 'ready', ready
    assert ready['chunk_count'] > 0
    assert ready['updated_at'] >= created['updated_at']

    # Get by id returns the full document including parsed_text.
    detail = client.get(f'/api/documents/{doc_id}')
    assert detail.status_code == 200
    assert 'parsed_text' in detail.json()

    # List omits parsed_text and includes the document.
    listing = client.get('/api/documents', params={'limit': 500})
    assert listing.status_code == 200
    body = listing.json()
    assert doc_id in [d['id'] for d in body['items']]
    assert all('parsed_text' not in item for item in body['items'])

    # Tag filter returns exactly our document; a bogus tag returns nothing.
    filtered = client.get('/api/documents', params={'tag': tag, 'limit': 500})
    assert [d['id'] for d in filtered.json()['items']] == [doc_id]
    empty = client.get('/api/documents', params={'tag': 'nonexistent-tag-xyz'})
    assert empty.json()['items'] == []

    # Tags endpoint returns sorted, de-duplicated tags including ours.
    tag_list = client.get('/api/tags').json()['tags']
    assert tag in tag_list
    assert len(tag_list) == len(set(tag_list))
    assert tag_list == sorted(tag_list)

    # Re-upload identical bytes → dedup hit: 200 + same id, no new document.
    dup = _upload(client, content=content, filename='renamed.md', tags=tag)
    assert dup.status_code == 200, dup.text
    assert dup.json()['id'] == doc_id

    # Delete → 204, then get-by-id 404.
    assert client.delete(f'/api/documents/{doc_id}').status_code == 204
    assert client.get(f'/api/documents/{doc_id}').status_code == 404


def test_unsupported_extension_rejected(client: httpx.Client) -> None:
    resp = _upload(client, content=b'print("hi")', filename='script.py', tags='')
    assert resp.status_code == 422, resp.text


def test_get_unknown_id_returns_404(client: httpx.Client) -> None:
    assert client.get('/api/documents/00000000-0000-0000-0000-000000000000').status_code == 404


def test_delete_unknown_id_returns_404(client: httpx.Client) -> None:
    assert client.delete('/api/documents/00000000-0000-0000-0000-000000000000').status_code == 404


def test_get_malformed_id_returns_404(client: httpx.Client) -> None:
    assert client.get('/api/documents/not-a-uuid').status_code == 404
