import pytest

from areopage import (
    AgentName,
    ConfidenceAssessment,
    Finding,
    FindingCategory,
    Severity,
    SourceDocument,
    SourceDocumentMetadata,
)


@pytest.fixture
def metadata() -> SourceDocumentMetadata:
    return SourceDocumentMetadata(
        filename="rapport.txt",
        media_type="text/plain",
        size_bytes=42,
        language="fr",
        origin="tests",
    )


@pytest.fixture
def document(metadata: SourceDocumentMetadata) -> SourceDocument:
    return SourceDocument.from_content(
        content="Contenu du rapport à analyser.", metadata=metadata
    )


@pytest.fixture
def finding() -> Finding:
    return Finding(
        author=AgentName.CLAUDE_CODE,
        category=FindingCategory.ACCURACY,
        severity=Severity.HIGH,
        title="Chiffre incohérent",
        description="Le total de la page 3 ne correspond pas au détail.",
    )


@pytest.fixture
def confidence() -> ConfidenceAssessment:
    return ConfidenceAssessment(score=72.5, rationale="Sources partielles.")
