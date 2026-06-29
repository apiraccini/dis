from __future__ import annotations

import hashlib

__all__ = ['FakeEmbedder']


class FakeEmbedder:
    """Deterministic, network-free embedder for e2e runs (settings.use_fake_embedder)."""

    def __init__(self, *, dimensions: int) -> None:
        self._dimensions = dimensions

    @property
    def dimension(self) -> int:
        return self._dimensions

    async def embed(self, texts: list[str]) -> list[list[float]]:
        vecs: list[list[float]] = []
        for text in texts:
            digest = hashlib.sha256(text.encode()).digest()
            vecs.append([digest[i % len(digest)] / 255.0 for i in range(self._dimensions)])
        return vecs
