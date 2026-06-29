from src.core.errors import DocumentNotFoundError, DuplicateDocumentError


def test_duplicate_document_error_is_exception_subclass() -> None:
    assert issubclass(DuplicateDocumentError, Exception)


def test_duplicate_document_error_carries_message() -> None:
    err = DuplicateDocumentError('hash already exists: abc123')
    assert str(err) == 'hash already exists: abc123'


def test_document_not_found_error_is_exception_subclass() -> None:
    assert issubclass(DocumentNotFoundError, Exception)


def test_document_not_found_error_carries_message() -> None:
    err = DocumentNotFoundError('no document with id 00000...')
    assert str(err) == 'no document with id 00000...'


def test_errors_are_distinct_types() -> None:
    assert DuplicateDocumentError is not DocumentNotFoundError
    assert not issubclass(DuplicateDocumentError, DocumentNotFoundError)
    assert not issubclass(DocumentNotFoundError, DuplicateDocumentError)
