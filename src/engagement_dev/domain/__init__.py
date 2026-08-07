"""Small, immutable domain objects with explicit evidence traceability."""

from dataclasses import dataclass
from enum import StrEnum


class EvidenceCategory(StrEnum):
    """The provenance of a claim; inference is deliberately not observation."""

    PUBLIC_FACT = "PUBLIC_FACT"
    OBSERVED_BEHAVIOR = "OBSERVED_BEHAVIOR"
    STAKEHOLDER_STATEMENT = "STAKEHOLDER_STATEMENT"
    INFERENCE = "INFERENCE"
    PUBLIC_MARKET_DATA = "PUBLIC_MARKET_DATA"
    INDUSTRY_PATTERN = "INDUSTRY_PATTERN"
    OBSERVED_TECHNOLOGY_PATTERN = "OBSERVED_TECHNOLOGY_PATTERN"
    PROVIDER_EXPERIENCE = "PROVIDER_EXPERIENCE"


DIRECT_EVIDENCE_CATEGORIES = frozenset(
    {
        EvidenceCategory.PUBLIC_FACT,
        EvidenceCategory.OBSERVED_BEHAVIOR,
        EvidenceCategory.STAKEHOLDER_STATEMENT,
        EvidenceCategory.PUBLIC_MARKET_DATA,
        EvidenceCategory.INDUSTRY_PATTERN,
        EvidenceCategory.OBSERVED_TECHNOLOGY_PATTERN,
        EvidenceCategory.PROVIDER_EXPERIENCE,
    }
)


@dataclass(frozen=True)
class Market:
    id: str
    name: str
    account_ids: tuple[str, ...]
    description: str = ""


@dataclass(frozen=True)
class MarketEvidence:
    """A sourced market-level observation, not evidence about an account."""

    id: str
    market_id: str
    description: str
    category: EvidenceCategory
    source: str

    @property
    def is_observed(self) -> bool:
        return self.category in DIRECT_EVIDENCE_CATEGORIES


@dataclass(frozen=True)
class MarketCharacteristic:
    """An observable market pattern that may make problem-class research relevant."""

    id: str
    market_id: str
    description: str
    relevant_problem_class_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class MarketHypothesis:
    """A cautious justification for research; it never establishes customer need."""

    id: str
    market_id: str
    cautious_statement: str
    relevant_problem_class_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    assumptions: tuple[str, ...]
    reason_for_investigation: str


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


@dataclass(frozen=True)
class Capability:
    """A skill the provider can demonstrate, independent of any prospect."""

    identifier: str
    name: str
    description: str


@dataclass(frozen=True)
class ProblemClass:
    """A recognizable problem category and the capabilities relevant to it."""

    identifier: str
    name: str
    description: str
    relevant_capability_ids: tuple[str, ...]


@dataclass(frozen=True)
class ProofArtifact:
    """Fictional educational work that demonstrates named capabilities."""

    identifier: str
    name: str
    description: str
    capability_ids: tuple[str, ...]


@dataclass(frozen=True)
class OfferBoundary:
    identifier: str
    statement: str


@dataclass(frozen=True)
class CapabilityProfile:
    provider_name: str
    capabilities: tuple[Capability, ...]
    proof_artifacts: tuple[ProofArtifact, ...]
    boundaries: tuple[OfferBoundary, ...]


@dataclass(frozen=True)
class ServiceOffer:
    identifier: str
    statement: str
    capability_ids: tuple[str, ...]
    problem_classes: tuple[ProblemClass, ...]
    proof_artifact_ids: tuple[str, ...]
    boundaries: tuple[OfferBoundary, ...]
