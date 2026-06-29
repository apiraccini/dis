from __future__ import annotations

from src.services.adapters.semchunk_chunker import SemchunkChunker
from src.services.protocols import Chunker


def test_satisfies_chunker_protocol() -> None:
    assert isinstance(SemchunkChunker(chunk_size=128), Chunker)


def test_empty_input_returns_empty_list() -> None:
    chunker = SemchunkChunker(chunk_size=128)

    assert chunker.chunk('') == []
    assert chunker.chunk('   \n\t  ') == []


def test_long_text_is_split_within_token_budget() -> None:
    # Each word is at least 1 token; force a split well under a long text.
    chunker = SemchunkChunker(chunk_size=8)
    text = ' '.join(f'word{i}' for i in range(50))

    chunks = chunker.chunk(text)

    assert len(chunks) > 1
    # Every chunk must fit within the token budget (8 tokens).
    import tiktoken

    enc = tiktoken.get_encoding('cl100k_base')
    assert all(len(enc.encode(c)) <= 8 for c in chunks)
    # Reassembling the chunks must reproduce the original text (semchunk preserves
    # all content; with overlap=0 concatenation is lossless).
    assert ''.join(chunks).replace(' ', '') == text.replace(' ', '')


def test_short_text_returns_single_chunk() -> None:
    chunker = SemchunkChunker(chunk_size=128)

    chunks = chunker.chunk('hello world this is short')

    assert chunks == ['hello world this is short']


def test_respects_configured_overlap() -> None:
    chunker = SemchunkChunker(chunk_size=8, overlap=2)
    text = ' '.join(f'word{i}' for i in range(30))

    chunks = chunker.chunk(text)

    assert len(chunks) > 1
