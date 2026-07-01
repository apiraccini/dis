from __future__ import annotations

import asyncio

from fastembed import SparseTextEmbedding

from src.repositories.protocols import SparseVector

__all__ = ['FastEmbedSparseEmbedder']


class FastEmbedSparseEmbedder:
    """Sparse (BM25) embedder backed by FastEmbed, run locally (no network calls).

    FastEmbed's `embed` is synchronous CPU-bound work; it runs off-thread so it
    never blocks the event loop (mirrors MarkItDownParser's isolation pattern).
    """

    def __init__(self, *, model_name: str = 'Qdrant/bm25') -> None:
        self._model = SparseTextEmbedding(model_name=model_name)

    async def embed(self, texts: list[str]) -> list[SparseVector]:
        if not texts:
            return []

        def _do() -> list[SparseVector]:
            return [
                SparseVector(indices=emb.indices.tolist(), values=emb.values.tolist())
                for emb in self._model.embed(texts)
            ]

        return await asyncio.to_thread(_do)
