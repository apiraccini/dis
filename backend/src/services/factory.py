from __future__ import annotations

from dataclasses import dataclass

from qdrant_client import AsyncQdrantClient
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.config import Settings
from src.repositories.document_repo import SqlModelDocumentRepository
from src.repositories.protocols import VectorStore
from src.services.adapters.markitdown_parser import MarkItDownParser
from src.services.adapters.openrouter_embedder import OpenRouterEmbedder
from src.services.adapters.qdrant_vector_store import QdrantVectorStore
from src.services.adapters.semchunk_chunker import SemchunkChunker
from src.services.ingestion import IngestionService
from src.services.protocols import Chunker, Embedder, Parser

__all__ = ['Adapters', 'build_adapters', 'build_ingestion_service']


@dataclass(frozen=True)
class Adapters:
    """Startup-constructed singletons for the ingestion pipeline.

    The document repository is intentionally NOT here — it is request-scoped
    (needs an AsyncSession); see `build_ingestion_service`.
    """

    parser: Parser
    chunker: Chunker
    embedder: Embedder
    query_embedder: Embedder
    vectors: VectorStore  # concrete: lifespan calls `.provision(dim)`


def build_adapters(settings: Settings) -> Adapters:
    qdrant = AsyncQdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
    vectors = QdrantVectorStore(client=qdrant, collection=settings.qdrant_collection)

    parser = MarkItDownParser()
    chunker = SemchunkChunker(
        chunk_size=settings.chunk_size_tokens,
        overlap=settings.chunk_overlap_tokens,
    )
    embedder = OpenRouterEmbedder(
        model=settings.embedding_model,
        dimensions=settings.embedding_dimensions,
        batch_size=settings.embedding_batch_size,
        input_type=settings.embedding_input_type_document,
        base_url=settings.embedding_base_url,
        api_key=settings.openrouter_api_key,
    )
    query_embedder = OpenRouterEmbedder(
        model=settings.embedding_model,
        dimensions=settings.embedding_dimensions,
        batch_size=settings.embedding_batch_size,
        input_type=settings.embedding_input_type_query,
        base_url=settings.embedding_base_url,
        api_key=settings.openrouter_api_key,
    )
    return Adapters(
        parser=parser,
        chunker=chunker,
        embedder=embedder,
        query_embedder=query_embedder,
        vectors=vectors,
    )


def build_ingestion_service(session: AsyncSession, adapters: Adapters) -> IngestionService:
    """Assemble an IngestionService for one request (session-scoped repo)."""
    documents = SqlModelDocumentRepository(session)
    return IngestionService(
        parser=adapters.parser,
        chunker=adapters.chunker,
        embedder=adapters.embedder,
        documents=documents,
        vectors=adapters.vectors,
    )
