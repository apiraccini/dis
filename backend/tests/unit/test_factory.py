from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.core.config import Settings
from src.services.factory import Adapters, build_adapters, build_ingestion_service
from src.services.ingestion import IngestionService


def test_build_adapters_returns_adapters_with_all_fields() -> None:
    settings = Settings(
        qdrant_url='http://test:6333',
        qdrant_collection='test-collection',
        openrouter_api_key='sk-test',
        embedding_model='test-model',
        embedding_dimensions=8,
        embedding_batch_size=2,
    )

    with patch('src.services.factory.AsyncQdrantClient') as mock_qdrant_cls:
        mock_client = MagicMock()
        mock_qdrant_cls.return_value = mock_client
        adapters = build_adapters(settings)

    assert isinstance(adapters, Adapters)
    assert adapters.parser is not None
    assert adapters.chunker is not None
    assert adapters.embedder is not None
    assert adapters.query_embedder is not None
    assert adapters.sparse_embedder is not None
    assert adapters.vectors is not None

    # Verify Qdrant client was constructed with the right args
    mock_qdrant_cls.assert_called_once_with(url='http://test:6333')


def test_build_adapters_sets_different_input_types() -> None:
    """Document and query embedders use different input_type values."""
    settings = Settings(
        qdrant_url='http://test:6333',
        embedding_input_type_document='search_document',
        embedding_input_type_query='search_query',
        openrouter_api_key='sk-test',
    )

    with patch('src.services.factory.AsyncQdrantClient') as mock_qdrant:
        mock_qdrant.return_value = MagicMock()
        with patch('src.services.factory.OpenRouterEmbedder') as mock_emb_cls:
            build_adapters(settings)

    # Both embedder and query_embedder constructed with correct input_type
    doc_call = mock_emb_cls.call_args_list[0]
    query_call = mock_emb_cls.call_args_list[1]
    assert doc_call.kwargs['input_type'] == 'search_document'
    assert query_call.kwargs['input_type'] == 'search_query'


def test_build_ingestion_service_returns_ingestion_service() -> None:
    session = MagicMock()
    adapters = Adapters(
        parser=MagicMock(),
        chunker=MagicMock(),
        embedder=MagicMock(),
        query_embedder=MagicMock(),
        sparse_embedder=MagicMock(),
        vectors=MagicMock(),
    )

    service = build_ingestion_service(session, adapters)

    assert isinstance(service, IngestionService)
    assert service._parser is adapters.parser
    assert service._chunker is adapters.chunker
    assert service._embedder is adapters.embedder
    assert service._vectors is adapters.vectors


def test_build_ingestion_service_creates_sql_repo_with_session() -> None:
    session = MagicMock()
    adapters = Adapters(
        parser=MagicMock(),
        chunker=MagicMock(),
        embedder=MagicMock(),
        query_embedder=MagicMock(),
        sparse_embedder=MagicMock(),
        vectors=MagicMock(),
    )

    with patch('src.services.factory.SqlModelDocumentRepository') as mock_repo_cls:
        service = build_ingestion_service(session, adapters)

    mock_repo_cls.assert_called_once_with(session)
    assert service._documents is mock_repo_cls.return_value
