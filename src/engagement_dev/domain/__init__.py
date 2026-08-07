"""Small, immutable domain objects with explicit evidence traceability."""

from dataclasses import dataclass
from enum import StrEnum


class EvidenceCategory(StrEnum):
    """The provenance of a claim; inference is deliberately not observation."""

    PUBLIC_FACT = "PUBLIC_FACT"
    OBSERVED_BEHAVIOR = "OBSERVED_BEHAVIOR"
    STAKEHOLDER_STATEMENT = "STAKEHOLDER_STATEMENT"
    INFERENCE = "INFERENCE"


DIRECT_EVIDENCE_CATEGORIES = frozenset(
    {
        EvidenceCategory.PUBLIC_FACT,
        EvidenceCategory.OBSERVED_BEHAVIOR,
        EvidenceCategory.STAKEHOLDER_STATEMENT,
    }
)


@dataclass(frozen=True)
class Market:
    id: str
    name: str
    account_ids: tuple[str, ...]


@dataclass(frozen=True)
class Account:
    id: str
    name: str
    market_id: str


@dataclass(frozen=True)
class ObservedSignal:
    id: str
    account_id: str
    description: str
    category: EvidenceCategory
    source: str

    @property
    def is_direct_evidence(self) -> bool:
        return self.category in DIRECT_EVIDENCE_CATEGORIES


@dataclass(frozen=True)
class OpportunityHypothesis:
    id: str
    account_id: str
    cautious_statement: str
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class Contact:
    id: str
    account_id: str
    name: str
    role: str


@dataclass(frozen=True)
class Conversation:
    id: str
    contact_id: str
    statement_signal_ids: tuple[str, ...]


@dataclass(frozen=True)
class QualificationAssessment:
    id: str
    hypothesis_id: str
    condition_met: bool
    rationale: str
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class EngagementCandidate:
    id: str
    account_id: str
    hypothesis_id: str
    qualification_id: str


class UnsupportedHypothesisError(ValueError):
    """Raised when direct, account-specific evidence does not support a hypothesis."""


class UnqualifiedEngagementError(ValueError):
    """Raised when someone attempts to create an engagement prematurely."""
