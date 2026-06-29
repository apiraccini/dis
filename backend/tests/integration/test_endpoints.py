from __future__ import annotations

import io
from collections.abc import AsyncGenerator, Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.core.dependencies import (
    get_app_adapters,
    get_document_repository,
    get_ingestion_service,
)
from src.models.document import Document
from src.repositories.in_memory import InMemoryDocumentRepository, InMemoryVectorStore
from src.repositories.protocols import DocumentRepository
from src.services.factory import Adapters
from src.services.ingestion import IngestionService
from tests._fakes import FakeChunker, FakeEmbedder, FakeParser

pytestmark = pytest.mark.integration

PARSED_TEXT = 'content of the uploaded file'


@pytest.fixture
def docs() -> InMemoryDocumentRepository:
    return InMemoryDocumentRepository()


@pytest.fixture(autouse=True)
def _override_dependencies(
    app: FastAPI,
    docs: InMemoryDocumentRepository,
) -> None:
    vectors = InMemoryVectorStore()
    parser = FakeParser(text=PARSED_TEXT)
    chunker = FakeChunker(words_per_chunk=10)
    embedder = FakeEmbedder(dimension=4)

    adapters = Adapters(
        parser=parser, chunker=chunker, embedder=embedder, query_embedder=embedder, vectors=vectors
    )

    async def _get_service() -> AsyncGenerator[IngestionService, None]:
        service = IngestionService(
            parser=parser,
            chunker=chunker,
            embedder=embedder,
            documents=docs,
            vectors=vectors,
        )
        yield service

    async def _get_docs() -> AsyncGenerator[DocumentRepository, None]:
        yield docs

    app.dependency_overrides[get_app_adapters] = lambda: adapters
    app.dependency_overrides[get_ingestion_service] = _get_service
    app.dependency_overrides[get_document_repository] = _get_docs


@pytest.fixture(autouse=True)
def _clear_overrides(app: FastAPI) -> Generator[None, None, None]:
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def app() -> FastAPI:
    from src.main import app

    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


# -- Seed helpers for tests that need data that's not ingested via upload --


async def _seed_doc(
    docs: InMemoryDocumentRepository,
    filename: str,
    h: str,
    tags: list[str],
) -> None:
    await docs.create(
        Document(filename=filename, content_hash=h, parsed_text=f'text {h}', tags=tags),
    )


class TestUpload:
    def test_happy_path_returns_202(self, client: TestClient) -> None:
        resp = client.post(
            '/api/documents/upload',
            files={'file': ('report.pdf', io.BytesIO(b'some bytes'), 'application/pdf')},
            data={'tags': 'compliance, audit'},
        )
        assert resp.status_code == 202
        body = resp.json()
        assert 'id' in body
        assert body['status'] == 'processing'
        assert body['filename'] == 'report.pdf'
        assert body['tags'] == ['compliance', 'audit']
        assert 'parsed_text' in body

    def test_dedup_hit_returns_200(self, client: TestClient) -> None:
        resp1 = client.post(
            '/api/documents/upload',
            files={'file': ('a.pdf', io.BytesIO(b'content'), 'application/pdf')},
            data={'tags': 'compliance'},
        )
        assert resp1.status_code == 202
        doc_id = resp1.json()['id']

        resp2 = client.post(
            '/api/documents/upload',
            files={'file': ('b.pdf', io.BytesIO(b'content'), 'application/pdf')},
            data={'tags': 'compliance'},
        )
        assert resp2.status_code == 200
        assert resp2.json()['id'] == doc_id

    def test_no_tags_returns_empty_tags_list(self, client: TestClient) -> None:
        resp = client.post(
            '/api/documents/upload',
            files={'file': ('doc.txt', io.BytesIO(b'hello'), 'text/plain')},
        )
        assert resp.status_code == 202
        assert resp.json()['tags'] == []

    def test_unsupported_file_type_returns_422(self, client: TestClient) -> None:
        resp = client.post(
            '/api/documents/upload',
            files={'file': ('script.py', io.BytesIO(b'print(1)'), 'text/x-python')},
        )
        assert resp.status_code == 422


class TestListDocuments:
    def test_empty_db_returns_empty_list(self, client: TestClient) -> None:
        resp = client.get('/api/documents')
        assert resp.status_code == 200
        body = resp.json()
        assert body['items'] == []
        assert body['total'] == 0

    async def test_returns_paginated_documents_and_omits_parsed_text(
        self,
        client: TestClient,
        docs: InMemoryDocumentRepository,
    ) -> None:
        await _seed_doc(docs, 'a.pdf', 'hash1', ['x'])
        await _seed_doc(docs, 'b.pdf', 'hash2', ['y'])

        resp = client.get('/api/documents?offset=0&limit=1')
        assert resp.status_code == 200
        body = resp.json()
        assert len(body['items']) == 1
        assert body['total'] == 2
        assert 'parsed_text' not in body['items'][0]

    async def test_filters_by_tag(
        self,
        client: TestClient,
        docs: InMemoryDocumentRepository,
    ) -> None:
        await _seed_doc(docs, 'a.pdf', 'hash1', ['compliance'])
        await _seed_doc(docs, 'b.pdf', 'hash2', ['hr'])

        resp = client.get('/api/documents?tag=compliance')
        assert resp.status_code == 200
        assert resp.json()['total'] == 1


class TestGetDocument:
    def test_returns_full_document_including_parsed_text(self, client: TestClient) -> None:
        upload_resp = client.post(
            '/api/documents/upload',
            files={'file': ('doc.txt', io.BytesIO(b'hello'), 'text/plain')},
        )
        doc_id = upload_resp.json()['id']

        resp = client.get(f'/api/documents/{doc_id}')
        assert resp.status_code == 200
        body = resp.json()
        assert body['id'] == doc_id
        assert body['parsed_text'] == PARSED_TEXT

    def test_404_on_missing_id(self, client: TestClient) -> None:
        resp = client.get('/api/documents/00000000-0000-0000-0000-000000000000')
        assert resp.status_code == 404

    def test_404_on_invalid_uuid(self, client: TestClient) -> None:
        resp = client.get('/api/documents/not-a-uuid')
        assert resp.status_code == 404


class TestDeleteDocument:
    def test_delete_cascades_and_returns_204(self, client: TestClient) -> None:
        upload_resp = client.post(
            '/api/documents/upload',
            files={'file': ('doc.txt', io.BytesIO(b'hello'), 'text/plain')},
        )
        doc_id = upload_resp.json()['id']

        resp = client.delete(f'/api/documents/{doc_id}')
        assert resp.status_code == 204

        get_resp = client.get(f'/api/documents/{doc_id}')
        assert get_resp.status_code == 404

    def test_delete_missing_returns_404(self, client: TestClient) -> None:
        resp = client.delete('/api/documents/00000000-0000-0000-0000-000000000000')
        assert resp.status_code == 404


class TestTags:
    def test_empty_db_returns_empty_list(self, client: TestClient) -> None:
        resp = client.get('/api/tags')
        assert resp.status_code == 200
        assert resp.json() == {'tags': []}

    async def test_returns_sorted_distinct_tags(
        self,
        client: TestClient,
        docs: InMemoryDocumentRepository,
    ) -> None:
        await _seed_doc(docs, 'a.pdf', 'hash1', ['compliance', 'audit'])
        await _seed_doc(docs, 'b.pdf', 'hash2', ['hr'])

        resp = client.get('/api/tags')
        assert resp.status_code == 200
        assert resp.json() == {'tags': ['audit', 'compliance', 'hr']}
