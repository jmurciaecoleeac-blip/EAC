"""Énumérations du domaine Aréopage.

Toutes les énumérations héritent de ``str`` afin de garantir une
sérialisation JSON stable (la valeur textuelle est la représentation
canonique).
"""

from enum import StrEnum


class AgentName(StrEnum):
    """Agents membres du conseil. Aucun appel réseau n'est effectué :
    ces noms servent uniquement à attribuer les productions."""

    CLAUDE_CODE = "claude_code"
    CODEX_CLI = "codex_cli"


class Severity(StrEnum):
    """Gravité d'un constat ou d'une donnée manquante."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class FindingCategory(StrEnum):
    """Catégorie d'un constat émis lors d'une analyse."""

    ACCURACY = "accuracy"
    CONSISTENCY = "consistency"
    COMPLETENESS = "completeness"
    METHODOLOGY = "methodology"
    COMPLIANCE = "compliance"
    SECURITY = "security"
    CLARITY = "clarity"
    OTHER = "other"


class ReviewPosition(StrEnum):
    """Position d'un agent lors de la revue croisée d'un constat."""

    CONFIRMED = "confirmed"
    CORRECTED = "corrected"
    REJECTED = "rejected"


class SessionStatus(StrEnum):
    """Cycle de vie d'une session du conseil."""

    CREATED = "created"
    FIRST_ROUND = "first_round"
    REVIEW = "review"
    SECOND_ROUND = "second_round"
    COMPLETED = "completed"
    FAILED = "failed"
