import pytest

from bookforge.util.schema import SchemaValidationError, validate_json

def test_book_schema_valid():
    data = {
        "schema_version": "1.0",
        "book_id": "test-book",
        "title": "Test",
        "genre": ["fantasy"],
        "targets": {},
        "voice": {},
        "invariants": [],
        "author_ref": "eldrik-vale/v1",
    }
    validate_json(data, "book")

def test_book_schema_missing_required():
    data = {
        "schema_version": "1.0",
        "title": "Test",
        "genre": ["fantasy"],
        "targets": {},
        "voice": {},
        "invariants": [],
        "author_ref": "eldrik-vale/v1",
    }
    with pytest.raises(SchemaValidationError):
        validate_json(data, "book")
