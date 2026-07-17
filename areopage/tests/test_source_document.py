import pytest
from pydantic import ValidationError

from areopage import SourceDocument, sha256_of_text
from areopage.models import SourceDocumentMetadata


def test_from_content_computes_valid_sha256(document: SourceDocument):
    assert document.sha256 == sha256_of_text(document.content)
    assert len(document.sha256) == 64


def test_mismatched_sha256_is_rejected(metadata: SourceDocumentMetadata):
    with pytest.raises(ValidationError, match="sha256"):
        SourceDocument(metadata=metadata, content="abc", sha256="0" * 64)


def test_malformed_sha256_is_rejected(metadata: SourceDocumentMetadata):
    with pytest.raises(ValidationError):
        SourceDocument(metadata=metadata, content="abc", sha256="pas-un-hash")


def test_uppercase_sha256_is_normalized(metadata: SourceDocumentMetadata):
    digest = sha256_of_text("abc")
    doc = SourceDocument(metadata=metadata, content="abc", sha256=digest.upper())
    assert doc.sha256 == digest


def test_document_is_immutable(document: SourceDocument):
    with pytest.raises(ValidationError):
        document.content = "contenu falsifié"
    with pytest.raises(ValidationError):
        document.metadata.filename = "autre.txt"


def test_document_id_is_uuid(document: SourceDocument):
    from uuid import UUID

    assert isinstance(document.id, UUID)


def test_naive_datetime_rejected_in_metadata():
    from datetime import datetime

    with pytest.raises(ValidationError):
        SourceDocumentMetadata(
            filename="a.txt",
            size_bytes=1,
            ingested_at=datetime(2026, 7, 17, 12, 0, 0),  # sans fuseau
        )
