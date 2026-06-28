class DuplicateDocumentError(Exception):
    """Raised when creating a document whose content hash already exists."""


class DocumentNotFoundError(Exception):
    """Raised when a document required for an operation does not exist."""


__all__ = ['DocumentNotFoundError', 'DuplicateDocumentError']
