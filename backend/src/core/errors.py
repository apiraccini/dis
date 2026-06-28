"""Domain exceptions shared across repository implementations.

Raised by repositories so service and MCP layers depend on the contract,
not on data-layer specifics (e.g. SQLModel IntegrityError / asyncpg errors).
"""


class DuplicateDocumentError(Exception):
    """Raised when creating a document whose content hash already exists."""


class DocumentNotFoundError(Exception):
    """Raised when a document required for an operation does not exist."""


__all__ = ['DocumentNotFoundError', 'DuplicateDocumentError']
