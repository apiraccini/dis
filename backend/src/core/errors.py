class DuplicateDocumentError(Exception):
    """Raised when creating a document whose content hash already exists."""


class DocumentNotFoundError(Exception):
    """Raised when a document required for an operation does not exist."""


class ParseError(Exception):
    """Raised when a document cannot be parsed into text."""


class EmbeddingError(Exception):
    """Raised when the embedding provider fails to embed text."""


__all__ = ['DocumentNotFoundError', 'DuplicateDocumentError', 'EmbeddingError', 'ParseError']
