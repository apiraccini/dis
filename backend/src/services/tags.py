from __future__ import annotations

from src.repositories.protocols import DocumentRepository


async def list_tags(documents: DocumentRepository) -> list[str]:
    """Return all unique tags sorted alphabetically."""
    return await documents.list_all_tags()
