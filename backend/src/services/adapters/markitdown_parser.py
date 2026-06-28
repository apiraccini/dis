from __future__ import annotations

import asyncio
import io
import os

from markitdown import MarkItDown, MarkItDownException, UnsupportedFormatException

from src.core.errors import ParseError

__all__ = ['MarkItDownParser']

# Extensions MarkItDown handles for this KB (documents + plain/markdown text).
# Anything else is rejected up front so callers get a predictable ParseError
# rather than markitdown's fall-through plaintext/sniffing behavior.
_SUPPORTED_EXTENSIONS: frozenset[str] = frozenset(
    {
        '.pdf',
        '.docx',
        '.pptx',
        '.xlsx',
        '.txt',
        '.md',
        '.markdown',
        '.csv',
        '.json',
        '.html',
        '.htm',
    }
)


class MarkItDownParser:
    """Parser backed by MarkItDown — converts uploads to Markdown text."""

    def __init__(self) -> None:
        self._md = MarkItDown()

    async def parse(self, content: bytes, filename: str) -> str:
        ext = os.path.splitext(filename)[1].lower()
        if ext not in _SUPPORTED_EXTENSIONS:
            raise ParseError(f'failed to parse {filename!r}: unsupported extension {ext!r}')

        def _do() -> str:
            try:
                result = self._md.convert_stream(io.BytesIO(content), file_extension=ext or None)
            except (UnsupportedFormatException, MarkItDownException) as exc:
                raise ParseError(f'failed to parse {filename!r}: {exc}') from exc
            return result.text_content

        text = await asyncio.to_thread(_do)
        if not text or not text.strip():
            raise ParseError(f'failed to parse {filename!r}: produced no text')
        return text
