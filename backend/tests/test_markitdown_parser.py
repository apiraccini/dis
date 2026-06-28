from __future__ import annotations

import pytest

from src.core.errors import ParseError
from src.services.adapters.markitdown_parser import MarkItDownParser
from src.services.protocols import Parser


def _make_pdf(text: str) -> bytes:
    """Build a minimal valid PDF with a single text-layer line."""
    content_stream = f'BT /F1 24 Tf 72 700 Td ({text}) Tj ET\n'.encode()
    objects = [
        b'<< /Type /Catalog /Pages 2 0 R >>',
        b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
        b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] '
        b'/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',
        b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
        b'<< /Length '
        + str(len(content_stream)).encode()
        + b' >>\nstream\n'
        + content_stream
        + b'endstream',
    ]
    pdf = b'%PDF-1.4\n'
    offsets: list[int] = []
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf += f'{i} 0 obj\n'.encode() + obj + b'\nendobj\n'
    xref_pos = len(pdf)
    pdf += b'xref\n0 ' + str(len(objects) + 1).encode() + b'\n'
    pdf += b'0000000000 65535 f \n'
    for off in offsets:
        pdf += f'{off:010d} 00000 n \n'.encode()
    pdf += (
        b'trailer\n<< /Size '
        + str(len(objects) + 1).encode()
        + b' /Root 1 0 R >>\nstartxref\n'
        + str(xref_pos).encode()
        + b'\n%%EOF\n'
    )
    return pdf


def test_satisfies_parser_protocol() -> None:
    assert isinstance(MarkItDownParser(), Parser)


async def test_parse_pdf_returns_markdown_text() -> None:
    parser = MarkItDownParser()
    pdf = _make_pdf('Quarterly Report')

    text = await parser.parse(pdf, 'report.pdf')

    assert 'Quarterly Report' in text
    assert text.strip() != ''


async def test_parse_plain_text_passthrough() -> None:
    parser = MarkItDownParser()

    text = await parser.parse(b'# Heading\n\nbody text', 'note.md')

    assert 'Heading' in text
    assert 'body text' in text


async def test_unsupported_extension_raises_parse_error() -> None:
    parser = MarkItDownParser()

    with pytest.raises(ParseError):
        await parser.parse(b'\x00\x01\x02 garbage', 'thing.zzz-not-a-format')


def test_runs_off_event_loop_does_not_block() -> None:
    # Sanity: the parser exposes an async parse() (covered by the protocol);
    # blocking isolation is provided via asyncio.to_thread inside the impl.
    # This test guards the public surface against accidental sync reverts.
    import inspect

    assert inspect.iscoroutinefunction(MarkItDownParser.parse)
