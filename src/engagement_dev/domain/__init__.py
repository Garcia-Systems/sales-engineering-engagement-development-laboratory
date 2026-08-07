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


class SignalType(StrEnum):
    HIRING = "HIRING"
    EXPANSION = "EXPANSION"
    NEW_LOCATION = "NEW_LOCATION"
    NEW_PRODUCT_OR_SERVICE = "NEW_PRODUCT_OR_SERVICE"
    TECHNOLOGY_CHANGE = "TECHNOLOGY_CHANGE"
    PLATFORM_MIGRATION = "PLATFORM_MIGRATION"
    ORGANIZATIONAL_CHANGE = "ORGANIZATIONAL_CHANGE"
    ACQUISITION = "ACQUISITION"
    PUBLIC_COMPLAINT = "PUBLIC_COMPLAINT"
    PROCESS_CHANGE = "PROCESS_CHANGE"
    REGULATORY_CHANGE = "REGULATORY_CHANGE"
    PROCUREMENT_ACTIVITY = "PROCUREMENT_ACTIVITY"
    LEADERSHIP_CHANGE = "LEADERSHIP_CHANGE"
    VENDOR_CHANGE = "VENDOR_CHANGE"


class SignalStrength(StrEnum):
    """Strength of the basis to investigate, never purchase probability."""

    WEAK = "WEAK"
    MODERATE = "MODERATE"
    STRONG = "STRONG"


class SignalPolarity(StrEnum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"


class HypothesisStatus(StrEnum):
    DRAFT = "DRAFT"
    SUPPORTED_FOR_VALIDATION = "SUPPORTED_FOR_VALIDATION"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    CONTRADICTED = "CONTRADICTED"
    VALIDATED = "VALIDATED"
    REFUTED = "REFUTED"


class AssumptionStatus(StrEnum):
    UNVALIDATED = "UNVALIDATED"
    SUPPORTED = "SUPPORTED"
    REFUTED = "REFUTED"


class UnknownCategory(StrEnum):
    PROBLEM_EXISTENCE = "PROBLEM_EXISTENCE"
    PROBLEM_SEVERITY = "PROBLEM_SEVERITY"
    CURRENT_PROCESS = "CURRENT_PROCESS"
    TECHNICAL_ENVIRONMENT = "TECHNICAL_ENVIRONMENT"
    BUSINESS_IMPACT = "BUSINESS_IMPACT"
    STAKEHOLDER = "STAKEHOLDER"
    URGENCY = "URGENCY"
    BUDGET = "BUDGET"
    DECISION_PROCESS = "DECISION_PROCESS"
    EXTERNAL_HELP_ACCEPTANCE = "EXTERNAL_HELP_ACCEPTANCE"


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
    signal_type: SignalType | None = None
    supporting_evidence: tuple[AccountEvidence, ...] = ()
    observed_on: date | None = None
    freshness: EvidenceFreshness | None = None
    underlying_event_id: str = ""
    interpretation: "SignalInterpretation | None" = None
    polarity: SignalPolarity = SignalPolarity.POSITIVE

    def __post_init__(self) -> None:
        if not self.source.strip():
            raise ValueError("A signal requires supporting evidence provenance.")
        if self.supporting_evidence and any(
            item.account_id != self.account_id for item in self.supporting_evidence
        ):
            raise ValueError("Signal evidence must belong to the signal account.")

    @property
    def is_direct_evidence(self) -> bool:
        return self.category in DIRECT_EVIDENCE_CATEGORIES


@dataclass(frozen=True)
class SignalInterpretation:
    observation: str
    possible_meaning: str
    relevant_problem_class_ids: tuple[str, ...]
    unresolved_questions: tuple[str, ...]


@dataclass(frozen=True)
class SignalCluster:
    id: str
    account_id: str
    theme: str
    signals: tuple[ObservedSignal, ...]
    relevant_problem_class_ids: tuple[str, ...]
    cluster_interpretation: str
    unresolved_questions: tuple[str, ...]
    strength: SignalStrength

    def __post_init__(self) -> None:
        if len(self.signals) < 2:
            raise ValueError("A cluster requires at least two related signals.")
        if any(signal.account_id != self.account_id for signal in self.signals):
            raise ValueError("Cluster signals must belong to one account.")
        shared = (
            set(self.signals[0].interpretation.relevant_problem_class_ids)
            if self.signals[0].interpretation
            else set()
        )
        for signal in self.signals[1:]:
            shared &= (
                set(signal.interpretation.relevant_problem_class_ids)
                if signal.interpretation
                else set()
            )
        if not shared or not shared.intersection(self.relevant_problem_class_ids):
            raise ValueError(
                "Signals need a shared problem class; unrelated signals cannot be clustered."
            )


@dataclass(frozen=True)
class Assumption:
    """A necessary proposition that must never be presented as evidence."""

    id: str
    statement: str
    status: AssumptionStatus = AssumptionStatus.UNVALIDATED


@dataclass(frozen=True)
class HypothesisUnknown:
    category: UnknownCategory
    question: str


@dataclass(frozen=True)
class EvidenceChainLink:
    evidence_id: str
    signal_id: str


@dataclass(frozen=True)
class OpportunityHypothesis:
    """A provisional, evidence-linked explanation—not a confirmed problem."""

    id: str
    account_id: str
    cautious_statement: str
    evidence_ids: tuple[str, ...]
    supporting_signal_ids: tuple[str, ...] = ()
    signal_cluster_id: str = ""
    relevant_problem_class_ids: tuple[str, ...] = ()
    reasoning: str = ""
    assumptions: tuple[Assumption, ...] = ()
    unknowns: tuple[HypothesisUnknown, ...] = ()
    falsification_conditions: tuple[str, ...] = ()
    validation_questions: tuple[str, ...] = ()
    evidence_chain: tuple[EvidenceChainLink, ...] = ()
    status: HypothesisStatus = HypothesisStatus.DRAFT
    competing_group_id: str = ""


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
