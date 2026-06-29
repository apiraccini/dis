from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast

import pytest
from openai import AsyncOpenAI

from src.core.errors import EmbeddingError
from src.services.adapters.openrouter_embedder import OpenRouterEmbedder
from src.services.protocols import Embedder

pytestmark = pytest.mark.integration


class _FakeEmbeddings:
    def __init__(self, create_fn: Any) -> None:
        self._create_fn = create_fn
        self.calls: list[list[str]] = []

    async def create(
        self, *, model: str, input: list[str], dimensions: int, extra_body: Any
    ) -> Any:
        self.calls.append(list(input))
        return self._create_fn(input, dimensions, extra_body, model)


class _FakeClient:
    def __init__(self, create_fn: Any) -> None:
        self.embeddings = _FakeEmbeddings(create_fn)


def _vec(text: str, dim: int) -> list[float]:
    # Deterministic placeholder vector; values are irrelevant to the adapter.
    return [float(len(text) % 100) / 100.0] * dim


def test_satisfies_embedder_protocol() -> None:
    embedder = OpenRouterEmbedder(
        client=cast(AsyncOpenAI, _FakeClient(lambda *_: SimpleNamespace(data=[]))),
        model='m',
        dimensions=4,
        batch_size=8,
    )
    assert isinstance(embedder, Embedder)
    assert embedder.dimension == 4


async def test_batches_and_preserves_order() -> None:
    def create_fn(input, dimensions, extra_body, model):
        assert model == 'qwen/qwen3-embedding-8b'
        assert dimensions == 1536
        assert extra_body == {'input_type': 'search_document'}
        return SimpleNamespace(data=[SimpleNamespace(embedding=_vec(t, 1536)) for t in input])

    fake = _FakeClient(create_fn)
    embedder = OpenRouterEmbedder(
        client=cast(AsyncOpenAI, fake),
        model='qwen/qwen3-embedding-8b',
        dimensions=1536,
        batch_size=64,
    )

    texts = [f'text {i}' for i in range(70)]
    vectors = await embedder.embed(texts)

    assert len(vectors) == 70
    assert all(len(v) == 1536 for v in vectors)
    # Two batches: 64 then 6.
    assert [len(c) for c in fake.embeddings.calls] == [64, 6]
    # Order preserved: each returned vector encodes its source text length.
    assert vectors[0] == _vec('text 0', 1536)
    assert vectors[69] == _vec('text 69', 1536)


async def test_provider_error_wrapped_as_embedding_error() -> None:
    def create_fn(input, dimensions, extra_body, model):
        raise RuntimeError('openrouter 503')

    client = cast(AsyncOpenAI, _FakeClient(create_fn))
    embedder = OpenRouterEmbedder(client=client, model='m', dimensions=4, batch_size=8)

    with pytest.raises(EmbeddingError):
        await embedder.embed(['a', 'b'])


async def test_query_input_type_is_passed_through() -> None:
    seen: dict[str, str] = {}

    def create_fn(input, dimensions, extra_body, model):
        seen['input_type'] = extra_body['input_type']
        return SimpleNamespace(data=[SimpleNamespace(embedding=_vec(t, 4)) for t in input])

    client = cast(AsyncOpenAI, _FakeClient(create_fn))
    embedder = OpenRouterEmbedder(
        client=client, model='m', dimensions=4, batch_size=8, input_type='search_query'
    )

    await embedder.embed(['q'])

    assert seen['input_type'] == 'search_query'
