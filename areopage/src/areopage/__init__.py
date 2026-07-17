"""Aréopage — fondation technique V0.2.

Modèles de domaine stricts pour un conseil d'agents analysant des
documents en deux tours avec revue croisée. Aucune intégration réseau,
aucune interface graphique, aucun moteur de consolidation dans cette
version.
"""

from .enums import (
    AgentName,
    FindingCategory,
    ReviewPosition,
    Severity,
    SessionStatus,
)
from .models import (
    ConfidenceAssessment,
    CouncilSession,
    CouncilVerdict,
    Finding,
    FirstRoundAnalysis,
    MissingData,
    Recommendation,
    ReviewDecision,
    SecondRoundAnalysis,
    SourceDocument,
    SourceDocumentMetadata,
    sha256_of_text,
    utcnow,
)
from .storage import SessionRepository

__version__ = "0.2.0"

__all__ = [
    "AgentName",
    "FindingCategory",
    "ReviewPosition",
    "Severity",
    "SessionStatus",
    "ConfidenceAssessment",
    "CouncilSession",
    "CouncilVerdict",
    "Finding",
    "FirstRoundAnalysis",
    "MissingData",
    "Recommendation",
    "ReviewDecision",
    "SecondRoundAnalysis",
    "SourceDocument",
    "SourceDocumentMetadata",
    "SessionRepository",
    "sha256_of_text",
    "utcnow",
    "__version__",
]
