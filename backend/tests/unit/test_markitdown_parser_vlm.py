from __future__ import annotations

from unittest.mock import patch

from src.services.adapters.markitdown_parser import MarkItDownParser


def test_default_builds_plain_markitdown_without_plugins() -> None:
    with patch('src.services.adapters.markitdown_parser.MarkItDown') as mock_md:
        MarkItDownParser()

    mock_md.assert_called_once_with()


def test_use_vlm_builds_markitdown_with_plugins_and_llm_client() -> None:
    client = object()

    with patch('src.services.adapters.markitdown_parser.MarkItDown') as mock_md:
        MarkItDownParser(use_vlm=True, llm_client=client, llm_model='google/gemini-3.1-flash-lite')

    mock_md.assert_called_once_with(
        enable_plugins=True, llm_client=client, llm_model='google/gemini-3.1-flash-lite'
    )
