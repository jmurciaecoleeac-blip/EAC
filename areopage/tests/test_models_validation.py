from uuid import uuid4

import pytest
from pydantic import ValidationError

from areopage import (
    AgentName,
    ConfidenceAssessment,
    CouncilSession,
    CouncilVerdict,
    Finding,
    FindingCategory,
    FirstRoundAnalysis,
    MissingData,
    Recommendation,
    ReviewDecision,
    ReviewPosition,
    SecondRoundAnalysis,
    SessionStatus,
    Severity,
)


def test_finding_requires_author():
    with pytest.raises(ValidationError, match="author"):
        Finding(
            category=FindingCategory.ACCURACY,
            severity=Severity.LOW,
            title="t",
            description="d",
        )


def test_confidence_bounds():
    ConfidenceAssessment(score=0, rationale="borne basse")
    ConfidenceAssessment(score=100, rationale="borne haute")
    for bad in (-0.1, 100.1, 250):
        with pytest.raises(ValidationError):
            ConfidenceAssessment(score=bad, rationale="hors bornes")


@pytest.mark.parametrize("position", [ReviewPosition.CORRECTED, ReviewPosition.REJECTED])
def test_justification_required_for_corrected_and_rejected(position):
    with pytest.raises(ValidationError, match="justification obligatoire"):
        ReviewDecision(
            reviewer=AgentName.CODEX_CLI,
            finding_id=uuid4(),
            position=position,
        )
    decision = ReviewDecision(
        reviewer=AgentName.CODEX_CLI,
        finding_id=uuid4(),
        position=position,
        justification="Le calcul initial ignorait la TVA.",
    )
    assert decision.justification is not None


def test_justification_optional_for_confirmed():
    decision = ReviewDecision(
        reviewer=AgentName.CLAUDE_CODE,
        finding_id=uuid4(),
        position=ReviewPosition.CONFIRMED,
    )
    assert decision.justification is None


def test_extra_fields_forbidden(finding):
    with pytest.raises(ValidationError):
        Finding(**finding.model_dump(), champ_inconnu="x")


def test_first_and_second_round_analyses(document, finding, confidence):
    first = FirstRoundAnalysis(
        agent=AgentName.CLAUDE_CODE,
        document_id=document.id,
        findings=[finding],
        summary="Une incohérence majeure détectée.",
        confidence=confidence,
    )
    second = SecondRoundAnalysis(
        agent=AgentName.CODEX_CLI,
        document_id=document.id,
        review_decisions=[
            ReviewDecision(
                reviewer=AgentName.CODEX_CLI,
                finding_id=finding.id,
                position=ReviewPosition.CONFIRMED,
            )
        ],
        summary="Constat adverse confirmé.",
        confidence=confidence,
    )
    assert first.findings[0].author is AgentName.CLAUDE_CODE
    assert second.review_decisions[0].finding_id == finding.id


def test_full_session_assembly(document, finding, confidence):
    verdict = CouncilVerdict(
        summary="Document exploitable sous réserve de corrections.",
        retained_finding_ids=[finding.id],
        recommendations=[
            Recommendation(
                author=AgentName.CLAUDE_CODE,
                priority=Severity.HIGH,
                title="Corriger le total",
                description="Recalculer le total de la page 3.",
            )
        ],
        missing_data=[
            MissingData(
                identified_by=AgentName.CODEX_CLI,
                description="Annexe budgétaire absente.",
                impact=Severity.MEDIUM,
            )
        ],
        confidence=confidence,
    )
    session = CouncilSession(document=document, verdict=verdict)
    assert session.status is SessionStatus.CREATED
    session.status = SessionStatus.COMPLETED
    assert session.status is SessionStatus.COMPLETED
    with pytest.raises(ValidationError):
        session.status = "statut_inconnu"
