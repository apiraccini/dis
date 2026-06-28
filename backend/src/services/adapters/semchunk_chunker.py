from __future__ import annotations

import functools
from collections.abc import Callable

import semchunk
import tiktoken

__all__ = ['SemchunkChunker']


class SemchunkChunker:
    """Chunker backed by semchunk (semantic, token-budgeted)."""

    def __init__(
        self,
        *,
        chunk_size: int,
        overlap: int = 0,
        token_counter: Callable[[str], int] | None = None,
    ) -> None:
        self._chunk_size = chunk_size
        self._overlap = overlap if overlap and overlap > 0 else None
        if token_counter is None:
            enc = tiktoken.get_encoding('cl100k_base')
            token_counter = lambda s: len(enc.encode(s))  # noqa: E731
        # Memoize per-instance so repeated chunking of identical text is cheap.
        self._counter = functools.lru_cache(maxsize=4096)(token_counter)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []
        result = semchunk.chunk(
            text,
            self._chunk_size,
            self._counter,
            overlap=self._overlap,
        )
        # offsets=False (default) → semchunk returns list[str], not the tuple form.
        assert isinstance(result, list)
        return result
