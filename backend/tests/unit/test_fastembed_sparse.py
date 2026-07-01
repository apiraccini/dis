from __future__ import annotations

from src.repositories.protocols import SparseVector
from src.services.adapters.fastembed_sparse import FastEmbedSparseEmbedder
from src.services.protocols import SparseEmbedder


def test_satisfies_sparse_embedder_protocol() -> None:
    assert isinstance(FastEmbedSparseEmbedder(), SparseEmbedder)


async def test_embed_returns_one_sparse_vector_per_text() -> None:
    embedder = FastEmbedSparseEmbedder()

    vectors = await embedder.embed(['compliance policy renewal', 'onboarding checklist'])

    assert len(vectors) == 2
    assert all(isinstance(v, SparseVector) for v in vectors)
    assert all(len(v.indices) == len(v.values) for v in vectors)
    assert all(len(v.indices) > 0 for v in vectors)


async def test_embed_empty_input_returns_empty_list() -> None:
    embedder = FastEmbedSparseEmbedder()

    assert await embedder.embed([]) == []


async def test_shared_keyword_yields_shared_index() -> None:
    embedder = FastEmbedSparseEmbedder()

    a, b = await embedder.embed(['compliance audit report', 'quarterly compliance summary'])

    assert set(a.indices) & set(b.indices)
