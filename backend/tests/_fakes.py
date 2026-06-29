from __future__ import annotations

__all__ = ['FakeChunker', 'FakeEmbedder', 'FakeParser']


class FakeParser:
    """Returns a fixed parsed string. Raises ParseError for certain extensions."""

    _UNSUPPORTED: frozenset[str] = frozenset({'.py', '.exe', '.dll'})

    def __init__(self, text: str = 'parsed content') -> None:
        self._text = text
        self.calls: list[tuple[bytes, str]] = []

    async def parse(self, content: bytes, filename: str) -> str:
        import os

        from src.core.errors import ParseError

        self.calls.append((content, filename))
        ext = os.path.splitext(filename)[1].lower()
        if ext in self._UNSUPPORTED:
            raise ParseError(f'failed to parse {filename!r}: unsupported extension {ext!r}')
        return self._text


class FakeChunker:
    """Splits text into fixed-size word chunks."""

    def __init__(self, words_per_chunk: int = 2) -> None:
        self._words_per_chunk = words_per_chunk
        self.calls: list[str] = []

    def chunk(self, text: str) -> list[str]:
        self.calls.append(text)
        words = text.split()
        if not words:
            return []
        return [
            ' '.join(words[i : i + self._words_per_chunk])
            for i in range(0, len(words), self._words_per_chunk)
        ]


class FakeEmbedder:
    """Returns a deterministic vector per chunk (hash of text → fixed dim)."""

    def __init__(self, dimension: int = 4) -> None:
        self._dimension = dimension
        self.calls: list[list[str]] = []
        self.returns: list[list[list[float]]] = []

    @property
    def dimension(self) -> int:
        return self._dimension

    async def embed(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(list(texts))
        import hashlib

        vecs: list[list[float]] = []
        for t in texts:
            h = hashlib.sha256(t.encode()).digest()
            # Repeat hash bytes to fill the dimension, normalize to [0,1].
            raw = [h[i % len(h)] / 255.0 for i in range(self._dimension)]
            vecs.append(raw)
        self.returns.append(vecs)
        return vecs
