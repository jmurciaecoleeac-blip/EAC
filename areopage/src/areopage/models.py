"""Modèles de domaine stricts d'Aréopage (Pydantic 2).

Garanties transverses :

- identifiants UUID (v4 par défaut) ;
- toutes les dates portent un fuseau horaire (``AwareDatetime``) ;
- champs inconnus refusés (``extra="forbid"``) ;
- sérialisation JSON stable (clés triées, UTF-8, séparateurs compacts) ;
- le document source est immuable une fois construit.
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Annotated, Self
from uuid import UUID, uuid4

from pydantic import (
    AwareDatetime,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)

from .enums import (
    AgentName,
    FindingCategory,
    ReviewPosition,
    Severity,
    SessionStatus,
)

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
def _normalize_hex(value: object) -> object:
    return value.strip().lower() if isinstance(value, str) else value


Sha256Hex = Annotated[
    str,
    BeforeValidator(_normalize_hex),
    StringConstraints(pattern=r"^[0-9a-f]{64}$"),
]
ConfidenceScore = Annotated[float, Field(ge=0, le=100)]


def utcnow() -> datetime:
    """Horodatage courant en UTC, toujours avec fuseau."""
    return datetime.now(timezone.utc)


def sha256_of_text(text: str) -> str:
    """Empreinte SHA-256 hexadécimale du texte encodé en UTF-8."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class AreopageModel(BaseModel):
    """Socle commun : validation stricte et JSON stable."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    def to_stable_json(self) -> str:
        """Sérialisation JSON déterministe : clés triées, sans espaces
        superflus, caractères non-ASCII préservés."""
        return json.dumps(
            self.model_dump(mode="json"),
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    @classmethod
    def from_json(cls, payload: str) -> Self:
        return cls.model_validate_json(payload)


class FrozenModel(AreopageModel):
    """Variante immuable du socle."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class SourceDocumentMetadata(FrozenModel):
    """Métadonnées descriptives d'un document source. Immuables."""

    filename: NonEmptyStr
    media_type: NonEmptyStr = "text/plain"
    size_bytes: int = Field(ge=0)
    language: str | None = None
    origin: str | None = None
    ingested_at: AwareDatetime = Field(default_factory=utcnow)


class SourceDocument(FrozenModel):
    """Document soumis au conseil. Immuable : toute correction passe par
    l'ingestion d'un nouveau document."""

    id: UUID = Field(default_factory=uuid4)
    metadata: SourceDocumentMetadata
    content: str
    sha256: Sha256Hex

    @model_validator(mode="after")
    def _check_sha256_matches_content(self) -> Self:
        expected = sha256_of_text(self.content)
        if self.sha256 != expected:
            raise ValueError(
                "sha256 ne correspond pas au contenu du document "
                f"(attendu {expected}, reçu {self.sha256})"
            )
        return self

    @classmethod
    def from_content(
        cls, content: str, metadata: SourceDocumentMetadata
    ) -> "SourceDocument":
        return cls(metadata=metadata, content=content, sha256=sha256_of_text(content))


class Finding(AreopageModel):
    """Constat émis par un agent. L'auteur est obligatoire."""

    id: UUID = Field(default_factory=uuid4)
    author: AgentName
    category: FindingCategory
    severity: Severity
    title: NonEmptyStr
    description: NonEmptyStr
    evidence: str | None = None
    created_at: AwareDatetime = Field(default_factory=utcnow)


class ConfidenceAssessment(AreopageModel):
    """Auto-évaluation de confiance, bornée entre 0 et 100."""

    score: ConfidenceScore
    rationale: NonEmptyStr


class FirstRoundAnalysis(AreopageModel):
    """Analyse indépendante de premier tour d'un agent."""

    id: UUID = Field(default_factory=uuid4)
    agent: AgentName
    document_id: UUID
    findings: list[Finding] = Field(default_factory=list)
    summary: NonEmptyStr
    confidence: ConfidenceAssessment
    created_at: AwareDatetime = Field(default_factory=utcnow)


class ReviewDecision(AreopageModel):
    """Position d'un agent sur un constat d'un autre agent.

    Une justification est obligatoire pour ``CORRECTED`` et ``REJECTED``.
    """

    id: UUID = Field(default_factory=uuid4)
    reviewer: AgentName
    finding_id: UUID
    position: ReviewPosition
    justification: NonEmptyStr | None = None
    created_at: AwareDatetime = Field(default_factory=utcnow)

    @model_validator(mode="after")
    def _require_justification(self) -> Self:
        needs = (ReviewPosition.CORRECTED, ReviewPosition.REJECTED)
        if self.position in needs and self.justification is None:
            raise ValueError(
                f"justification obligatoire pour la position {self.position.value}"
            )
        return self


class SecondRoundAnalysis(AreopageModel):
    """Second tour : revue croisée des constats adverses et compléments."""

    id: UUID = Field(default_factory=uuid4)
    agent: AgentName
    document_id: UUID
    review_decisions: list[ReviewDecision] = Field(default_factory=list)
    new_findings: list[Finding] = Field(default_factory=list)
    summary: NonEmptyStr
    confidence: ConfidenceAssessment
    created_at: AwareDatetime = Field(default_factory=utcnow)


class MissingData(AreopageModel):
    """Donnée absente du document et nécessaire à l'analyse."""

    id: UUID = Field(default_factory=uuid4)
    identified_by: AgentName
    description: NonEmptyStr
    impact: Severity
    created_at: AwareDatetime = Field(default_factory=utcnow)


class Recommendation(AreopageModel):
    """Recommandation actionnable issue des travaux du conseil."""

    id: UUID = Field(default_factory=uuid4)
    author: AgentName
    priority: Severity
    title: NonEmptyStr
    description: NonEmptyStr
    created_at: AwareDatetime = Field(default_factory=utcnow)


class CouncilVerdict(AreopageModel):
    """Verdict final. V0.2 : simple conteneur de données — aucun moteur
    de consolidation n'est fourni."""

    id: UUID = Field(default_factory=uuid4)
    summary: NonEmptyStr
    retained_finding_ids: list[UUID] = Field(default_factory=list)
    recommendations: list[Recommendation] = Field(default_factory=list)
    missing_data: list[MissingData] = Field(default_factory=list)
    confidence: ConfidenceAssessment
    issued_at: AwareDatetime = Field(default_factory=utcnow)


class CouncilSession(AreopageModel):
    """Session complète du conseil autour d'un document source."""

    id: UUID = Field(default_factory=uuid4)
    document: SourceDocument
    status: SessionStatus = SessionStatus.CREATED
    first_round: list[FirstRoundAnalysis] = Field(default_factory=list)
    second_round: list[SecondRoundAnalysis] = Field(default_factory=list)
    verdict: CouncilVerdict | None = None
    created_at: AwareDatetime = Field(default_factory=utcnow)
    updated_at: AwareDatetime = Field(default_factory=utcnow)
