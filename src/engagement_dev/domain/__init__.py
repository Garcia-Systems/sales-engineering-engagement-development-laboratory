"""Small, immutable domain objects with explicit evidence traceability."""

from dataclasses import dataclass
from datetime import date
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


class PublicSourceType(StrEnum):
    COMPANY_WEBSITE = "COMPANY_WEBSITE"
    PUBLIC_JOB_POSTING = "PUBLIC_JOB_POSTING"
    PRESS_RELEASE = "PRESS_RELEASE"
    PUBLIC_VENDOR_PAGE = "PUBLIC_VENDOR_PAGE"
    PUBLIC_SOCIAL_POST = "PUBLIC_SOCIAL_POST"
    PUBLIC_NEWS_ARTICLE = "PUBLIC_NEWS_ARTICLE"
    PUBLIC_DIRECTORY = "PUBLIC_DIRECTORY"


class SourceReliability(StrEnum):
    PRIMARY_PUBLIC_SOURCE = "PRIMARY_PUBLIC_SOURCE"
    SECONDARY_PUBLIC_SOURCE = "SECONDARY_PUBLIC_SOURCE"
    UNVERIFIED_PUBLIC_CLAIM = "UNVERIFIED_PUBLIC_CLAIM"


class EvidenceFreshness(StrEnum):
    CURRENT = "CURRENT"
    AGING = "AGING"
    STALE = "STALE"


class ResearchDimension(StrEnum):
    ORGANIZATION = "ORGANIZATION"
    OPERATIONS = "OPERATIONS"
    TECHNOLOGY = "TECHNOLOGY"
    CHANGE = "CHANGE"
    PEOPLE = "PEOPLE"


class ResearchClaimType(StrEnum):
    FACT = "FACT"
    OBSERVATION = "OBSERVATION"


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
    organization_type: str = ""
    location: str = ""
    public_description: str = ""
    observed_characteristics: tuple[str, ...] = ()
    evidence_references: tuple[str, ...] = ()
    research_status: str = "UNRESEARCHED"


@dataclass(frozen=True)
class AccountEvidence:
    """A sourced public observation about one account, before signal analysis."""

    id: str
    account_id: str
    description: str
    category: EvidenceCategory
    source: str
    relevant_problem_class_ids: tuple[str, ...] = ()
    is_negative: bool = False
    source_type: PublicSourceType | None = None
    source_reliability: SourceReliability | None = None
    observed_on: date | None = None
    dimension: ResearchDimension | None = None
    claim_type: ResearchClaimType = ResearchClaimType.OBSERVATION

    @property
    def is_observed(self) -> bool:
        return self.category in DIRECT_EVIDENCE_CATEGORIES


@dataclass(frozen=True)
class AccountInterpretation:
    """A cautious analyst reading of evidence; never an observed customer fact."""

    id: str
    account_id: str
    statement: str
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class ResearchUnknown:
    id: str
    account_id: str
    question: str
    dimension: ResearchDimension


@dataclass(frozen=True)
class EvidenceConflict:
    id: str
    account_id: str
    evidence_ids: tuple[str, ...]
    explanation: str
    requires_review: bool = True


@dataclass(frozen=True)
class CorroboratedObservation:
    statement: str
    evidence_ids: tuple[str, ...]
    explanation: str


@dataclass(frozen=True)
class AccountResearchBrief:
    """Public account research only; deliberately contains no qualification fields."""

    account: Account
    market: Market
    research_date: date
    evidence: tuple[AccountEvidence, ...]
    inferences: tuple[AccountInterpretation, ...]
    unknowns: tuple[ResearchUnknown, ...]
    conflicts: tuple[EvidenceConflict, ...]
    corroborated_observations: tuple[CorroboratedObservation, ...]
    relevant_problem_class_ids: tuple[str, ...]


@dataclass(frozen=True)
class AccountCandidate:
    """A reason to research an organization, not a prospect or opportunity."""

    account: Account
    selected_market: Market
    supporting_evidence: tuple[AccountEvidence, ...]
    relevant_market_characteristics: tuple[MarketCharacteristic, ...]
    relevant_problem_class_ids: tuple[str, ...]
    research_rationale: str


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
