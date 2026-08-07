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


class KnowledgeDomain(StrEnum):
    WORKFLOW = "WORKFLOW"
    TECHNOLOGY = "TECHNOLOGY"
    BUSINESS_IMPACT = "BUSINESS_IMPACT"
    FINANCE = "FINANCE"
    OPERATIONS = "OPERATIONS"
    STRATEGY = "STRATEGY"
    PROCUREMENT = "PROCUREMENT"
    IMPLEMENTATION = "IMPLEMENTATION"
    CUSTOMER_EXPERIENCE = "CUSTOMER_EXPERIENCE"
    MARKETING = "MARKETING"


class EvidenceProximity(StrEnum):
    DIRECT = "DIRECT"
    NEAR = "NEAR"
    INDIRECT = "INDIRECT"
    UNKNOWN = "UNKNOWN"


class OrganizationalRole(StrEnum):
    WORKFLOW_OWNER = "WORKFLOW_OWNER"
    TECHNICAL_STAKEHOLDER = "TECHNICAL_STAKEHOLDER"
    BUSINESS_STAKEHOLDER = "BUSINESS_STAKEHOLDER"
    ECONOMIC_STAKEHOLDER = "ECONOMIC_STAKEHOLDER"
    PROCUREMENT_STAKEHOLDER = "PROCUREMENT_STAKEHOLDER"
    EXECUTIVE_SPONSOR = "EXECUTIVE_SPONSOR"
    END_USER = "END_USER"
    INFLUENCER = "INFLUENCER"
    UNKNOWN = "UNKNOWN"


class AuthorityStatus(StrEnum):
    SUPPORTED = "SUPPORTED"
    UNKNOWN = "UNKNOWN"


class StakeholderClaimType(StrEnum):
    TITLE = "TITLE"
    ORGANIZATIONAL_ROLE = "ORGANIZATIONAL_ROLE"
    RESPONSIBILITY = "RESPONSIBILITY"
    RELATIONSHIP = "RELATIONSHIP"


@dataclass(frozen=True)
class StakeholderEvidence:
    id: str
    account_id: str
    claim_type: StakeholderClaimType
    claim: str
    source: str
    source_type: PublicSourceType

    def __post_init__(self) -> None:
        if not self.claim.strip() or not self.source.strip():
            raise ValueError("Stakeholder claims require public evidence provenance.")


@dataclass(frozen=True)
class QuestionProximity:
    validation_question: str
    domain: KnowledgeDomain
    proximity: EvidenceProximity


@dataclass(frozen=True)
class Stakeholder:
    """An evidence-backed view of a Contact, never an automatic buyer."""

    contact: Contact
    account_id: str
    title: str
    organizational_roles: tuple[OrganizationalRole, ...]
    responsibilities: tuple[str, ...]
    knowledge_domains: tuple[KnowledgeDomain, ...]
    question_proximities: tuple[QuestionProximity, ...]
    possible_relevance: str
    evidence: tuple[StakeholderEvidence, ...]
    purchasing_authority: AuthorityStatus = AuthorityStatus.UNKNOWN
    budget_authority: AuthorityStatus = AuthorityStatus.UNKNOWN
    procurement_authority: AuthorityStatus = AuthorityStatus.UNKNOWN
    technical_authority: AuthorityStatus = AuthorityStatus.UNKNOWN

    def __post_init__(self) -> None:
        if self.contact.account_id != self.account_id:
            raise ValueError("Stakeholder contact and account must match.")
        claims = {(item.claim_type, item.claim) for item in self.evidence}
        if (StakeholderClaimType.TITLE, self.title) not in claims:
            raise ValueError("A stakeholder title requires supporting evidence.")
        if any((StakeholderClaimType.RESPONSIBILITY, item) not in claims for item in self.responsibilities):
            raise ValueError("Every stakeholder responsibility requires supporting evidence.")
        if (
            any(item is not OrganizationalRole.UNKNOWN for item in self.organizational_roles)
            and not any(item.claim_type is StakeholderClaimType.ORGANIZATIONAL_ROLE for item in self.evidence)
        ):
            raise ValueError("A supported organizational role requires evidence.")
        if any(item.account_id != self.account_id for item in self.evidence):
            raise ValueError("Stakeholder evidence must belong to the account.")


class RelationshipType(StrEnum):
    REPORTS_TO = "REPORTS_TO"
    WORKS_WITH = "WORKS_WITH"
    SUPPORTS = "SUPPORTS"
    OVERSEES = "OVERSEES"
    UNKNOWN_RELATIONSHIP = "UNKNOWN_RELATIONSHIP"


@dataclass(frozen=True)
class StakeholderRelationship:
    source_contact_id: str
    target_contact_id: str
    relationship_type: RelationshipType
    evidence_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.relationship_type is not RelationshipType.UNKNOWN_RELATIONSHIP and not self.evidence_ids:
            raise ValueError("A known organizational relationship requires evidence.")
        if self.relationship_type is RelationshipType.UNKNOWN_RELATIONSHIP and self.evidence_ids:
            raise ValueError("An unknown relationship cannot cite evidence as support.")


@dataclass(frozen=True)
class ValidationQuestionMapping:
    question: str
    required_domains: tuple[KnowledgeDomain, ...]
    stakeholder_ids: tuple[str, ...]


@dataclass(frozen=True)
class StakeholderMap:
    account_id: str
    hypothesis_id: str
    stakeholders: tuple[Stakeholder, ...]
    relationships: tuple[StakeholderRelationship, ...]
    question_mappings: tuple[ValidationQuestionMapping, ...]


class ConversationStatus(StrEnum):
    PLANNED = "PLANNED"
    SIMULATED = "SIMULATED"
    COMPLETED = "COMPLETED"


class ConversationObjective(StrEnum):
    VALIDATE_OPPORTUNITY_HYPOTHESIS = "VALIDATE_OPPORTUNITY_HYPOTHESIS"


class ConversationStage(StrEnum):
    OPEN = "OPEN"
    CONTEXT = "CONTEXT"
    EXPLORE = "EXPLORE"
    CLARIFY = "CLARIFY"
    SUMMARIZE = "SUMMARIZE"
    NEXT_STEP = "NEXT_STEP"


class QuestionType(StrEnum):
    CURRENT_STATE = "CURRENT_STATE"
    CHANGE = "CHANGE"
    WORKFLOW = "WORKFLOW"
    IMPACT = "IMPACT"
    TECHNOLOGY = "TECHNOLOGY"
    STAKEHOLDER = "STAKEHOLDER"
    PRIORITY = "PRIORITY"
    HISTORY = "HISTORY"
    CONSTRAINT = "CONSTRAINT"
    NEXT_STEP = "NEXT_STEP"


class StatementRelationship(StrEnum):
    SUPPORTS = "SUPPORTS"
    REFINES = "REFINES"
    CONTRADICTS = "CONTRADICTS"
    NEUTRAL = "NEUTRAL"
    INTRODUCES_NEW_INFORMATION = "INTRODUCES_NEW_INFORMATION"


class HypothesisOutcome(StrEnum):
    HYPOTHESIS_STRENGTHENED = "HYPOTHESIS_STRENGTHENED"
    HYPOTHESIS_REFINED = "HYPOTHESIS_REFINED"
    HYPOTHESIS_REFUTED = "HYPOTHESIS_REFUTED"
    MORE_EVIDENCE_NEEDED = "MORE_EVIDENCE_NEEDED"
    NO_CURRENT_OPPORTUNITY = "NO_CURRENT_OPPORTUNITY"


@dataclass(frozen=True)
class ConversationQuestion:
    text: str
    question_type: QuestionType
    stage: ConversationStage


@dataclass(frozen=True)
class StakeholderStatement:
    """What a stakeholder said, not an automatically objective operational fact."""

    stakeholder_id: str
    statement: str
    topic: str
    evidence_category: EvidenceCategory
    relationship: StatementRelationship
    source_conversation_id: str
    id: str = ""

    def __post_init__(self) -> None:
        if self.evidence_category is not EvidenceCategory.STAKEHOLDER_STATEMENT:
            raise ValueError("A stakeholder statement requires STAKEHOLDER_STATEMENT evidence.")
        if not self.statement.strip() or not self.source_conversation_id:
            raise ValueError("A stakeholder statement requires content and conversation provenance.")


@dataclass(frozen=True)
class ConversationEvidence:
    """Separates a direct statement from its cautious analyst interpretation."""

    statement: StakeholderStatement
    interpretation: str


@dataclass(frozen=True)
class HypothesisRevision:
    original: OpportunityHypothesis
    refined: OpportunityHypothesis | None
    stakeholder_evidence: tuple[StakeholderStatement, ...]
    outcome: HypothesisOutcome


@dataclass(frozen=True)
class ConversationEvidenceLedger:
    known_before: tuple[str, ...]
    hypothesized_before: tuple[str, ...]
    unknown_before: tuple[str, ...]
    known_from_stakeholder: tuple[str, ...]
    still_unknown: tuple[str, ...]


@dataclass(frozen=True)
class Conversation:
    id: str
    contact_id: str
    statement_signal_ids: tuple[str, ...] = ()
    account_id: str = ""
    stakeholder_id: str = ""
    outreach_attempt_id: str = ""
    opportunity_hypothesis_id: str = ""
    objective: ConversationObjective = ConversationObjective.VALIDATE_OPPORTUNITY_HYPOTHESIS
    questions: tuple[ConversationQuestion, ...] = ()
    stakeholder_statements: tuple[StakeholderStatement, ...] = ()
    evidence_captured: tuple[ConversationEvidence, ...] = ()
    hypothesis_outcome: HypothesisOutcome = HypothesisOutcome.MORE_EVIDENCE_NEEDED
    unresolved_questions: tuple[str, ...] = ()
    next_step: str = ""
    status: ConversationStatus = ConversationStatus.PLANNED
    qualified_opportunity_created: bool = False

    def __post_init__(self) -> None:
        if self.qualified_opportunity_created:
            raise ValueError("Conversation completion cannot automatically create qualification.")
        if any(item.source_conversation_id != self.id for item in self.stakeholder_statements):
            raise ValueError("Stakeholder statements must retain this conversation as their source.")


@dataclass(frozen=True)
class QualificationAssessment:
    id: str
    hypothesis_id: str
    condition_met: bool
    rationale: str
    evidence_ids: tuple[str, ...]
    opportunity_hypothesis: OpportunityHypothesis | None = None
    refined_hypothesis: OpportunityHypothesis | None = None
    dimensions: tuple["QualificationDimension", ...] = ()
    unresolved_gaps: tuple[str, ...] = ()
    contradictions: tuple[str, ...] = ()
    outcome: "QualificationOutcome | None" = None
    explanation: str = ""
    recommended_next_action: str = ""

    def dimension(self, name: "QualificationDimensionName") -> "QualificationDimension":
        return next(item for item in self.dimensions if item.name is name)


@dataclass(frozen=True)
class EngagementCandidate:
    id: str
    account_id: str
    hypothesis_id: str
    qualification_id: str
    account: Account | None = None
    validated_problem_hypothesis: OpportunityHypothesis | None = None
    qualification_assessment: QualificationAssessment | None = None
    stakeholder_evidence: tuple[StakeholderStatement, ...] = ()
    known_stakeholders: tuple[Stakeholder, ...] = ()
    business_impact_evidence: tuple[str, ...] = ()
    current_approach: str = ""
    known_constraints: tuple[str, ...] = ()
    timing: str = ""
    unresolved_questions: tuple[str, ...] = ()
    engagement_objective: str = ""
    handoff_status: str = "NOT_READY"


class QualificationDimensionName(StrEnum):
    PROBLEM = "PROBLEM"
    IMPACT = "IMPACT"
    PRIORITY = "PRIORITY"
    OWNERSHIP = "OWNERSHIP"
    TIMING = "TIMING"
    CURRENT_APPROACH = "CURRENT_APPROACH"
    CONSTRAINTS = "CONSTRAINTS"
    DECISION_PROCESS = "DECISION_PROCESS"
    PROVIDER_FIT = "PROVIDER_FIT"
    EXTERNAL_HELP = "EXTERNAL_HELP"
    AGREED_INVESTIGATION = "AGREED_INVESTIGATION"
    BUDGET = "BUDGET"


class ProblemState(StrEnum):
    CONFIRMED = "CONFIRMED"
    PARTIAL = "PARTIAL"
    UNKNOWN = "UNKNOWN"
    REFUTED = "REFUTED"


class ImpactState(StrEnum):
    CONFIRMED = "CONFIRMED"
    PARTIAL = "PARTIAL"
    UNKNOWN = "UNKNOWN"
    NO_ACTIONABLE_IMPACT = "NO_ACTIONABLE_IMPACT"


class PriorityState(StrEnum):
    ACTIVE = "ACTIVE"
    EMERGING = "EMERGING"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"
    NOT_A_PRIORITY = "NOT_A_PRIORITY"


class OwnershipState(StrEnum):
    IDENTIFIED = "IDENTIFIED"
    PARTIAL = "PARTIAL"
    UNKNOWN = "UNKNOWN"


class TimingState(StrEnum):
    ACTIVE = "ACTIVE"
    UPCOMING = "UPCOMING"
    UNDEFINED = "UNDEFINED"
    DEFERRED = "DEFERRED"


class KnowledgeState(StrEnum):
    KNOWN = "KNOWN"
    PARTIAL = "PARTIAL"
    UNKNOWN = "UNKNOWN"


class ProviderFitState(StrEnum):
    SUPPORTED = "SUPPORTED"
    UNKNOWN = "UNKNOWN"
    NOT_A_FIT = "NOT_A_FIT"


class ExternalHelpState(StrEnum):
    OPEN = "OPEN"
    POSSIBLY_OPEN = "POSSIBLY_OPEN"
    UNKNOWN = "UNKNOWN"
    INTERNAL_ONLY = "INTERNAL_ONLY"
    NOT_INTERESTED = "NOT_INTERESTED"


class QualificationOutcome(StrEnum):
    QUALIFIED_FOR_ENGAGEMENT = "QUALIFIED_FOR_ENGAGEMENT"
    MORE_DISCOVERY_NEEDED = "MORE_DISCOVERY_NEEDED"
    NOT_CURRENT_PRIORITY = "NOT_CURRENT_PRIORITY"
    NO_ACTIONABLE_IMPACT = "NO_ACTIONABLE_IMPACT"
    NO_CLEAR_OWNER = "NO_CLEAR_OWNER"
    TIMING_NOT_ACTIVE = "TIMING_NOT_ACTIVE"
    EXTERNAL_HELP_NOT_ACCEPTED = "EXTERNAL_HELP_NOT_ACCEPTED"
    NOT_A_FIT = "NOT_A_FIT"
    NO_CURRENT_OPPORTUNITY = "NO_CURRENT_OPPORTUNITY"


@dataclass(frozen=True)
class QualificationDimension:
    """One explicit conclusion and the evidence that permits it."""

    name: QualificationDimensionName
    state: StrEnum
    evidence_ids: tuple[str, ...] = ()
    explanation: str = ""
    unknowns: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        unknown_states = {"UNKNOWN", "UNDEFINED"}
        if self.state.value not in unknown_states and not self.evidence_ids:
            raise ValueError(f"{self.name.value} {self.state.value} requires evidence.")


@dataclass(frozen=True)
class EngagementHandoff:
    account: Account
    problem: str
    evidence: tuple[StakeholderStatement, ...]
    business_impact: str
    priority: str
    owner: Stakeholder
    timing: str
    current_approach: str
    known_constraints: tuple[str, ...]
    external_help: str
    unknowns: tuple[str, ...]
    engagement_objective: str


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


class OutreachChannel(StrEnum):
    EMAIL = "EMAIL"
    PROFESSIONAL_NETWORK = "PROFESSIONAL_NETWORK"
    PHONE_PREPARATION = "PHONE_PREPARATION"
    IN_PERSON_PREPARATION = "IN_PERSON_PREPARATION"


class OutreachObjective(StrEnum):
    VALIDATE_HYPOTHESIS = "VALIDATE_HYPOTHESIS"


class OutreachStatus(StrEnum):
    DRAFT = "DRAFT"
    READY = "READY"
    SENT_SIMULATED = "SENT_SIMULATED"
    NO_RESPONSE = "NO_RESPONSE"
    REPLIED = "REPLIED"
    DECLINED = "DECLINED"


@dataclass(frozen=True)
class OutreachEvidence:
    """A public message claim and the account evidence that supports it."""

    claim: str
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class OutreachMessage:
    id: str
    account_id: str
    stakeholder_id: str
    hypothesis_id: str
    objective: OutreachObjective
    channel: OutreachChannel
    observation: str
    relevance: str
    credibility: str
    validation_question: str
    call_to_action: str
    factual_claims: tuple[OutreachEvidence, ...]
    credibility_proof_ids: tuple[str, ...]
    body: str


@dataclass(frozen=True)
class OutreachAttempt:
    """A simulation record. READY explicitly does not mean sent."""

    message: OutreachMessage
    status: OutreachStatus = OutreachStatus.DRAFT
    actual_message_sent: bool = False

    def __post_init__(self) -> None:
        if self.actual_message_sent:
            raise ValueError("This educational laboratory cannot send external communication.")


class FollowUpReason(StrEnum):
    NO_RESPONSE_TO_INITIAL_OUTREACH = "NO_RESPONSE_TO_INITIAL_OUTREACH"
    REQUESTED_FOLLOW_UP = "REQUESTED_FOLLOW_UP"
    TIMING_CHANGE = "TIMING_CHANGE"
    NEW_RELEVANT_EVIDENCE = "NEW_RELEVANT_EVIDENCE"
    OPEN_QUESTION = "OPEN_QUESTION"
    POST_CONVERSATION_NEXT_STEP = "POST_CONVERSATION_NEXT_STEP"
    QUALIFICATION_GAP = "QUALIFICATION_GAP"
    STAKEHOLDER_REFERRAL = "STAKEHOLDER_REFERRAL"


class FollowUpStatus(StrEnum):
    PLANNED = "PLANNED"
    READY = "READY"
    SENT_SIMULATED = "SENT_SIMULATED"
    REPLIED = "REPLIED"
    NO_RESPONSE = "NO_RESPONSE"
    DEFERRED = "DEFERRED"
    CLOSED = "CLOSED"


class StopReason(StrEnum):
    MAX_ATTEMPTS_REACHED = "MAX_ATTEMPTS_REACHED"
    EXPLICIT_DECLINE = "EXPLICIT_DECLINE"
    NO_LONGER_RELEVANT = "NO_LONGER_RELEVANT"
    HYPOTHESIS_REFUTED = "HYPOTHESIS_REFUTED"
    REQUESTED_NO_CONTACT = "REQUESTED_NO_CONTACT"
    TIMING_TOO_DISTANT = "TIMING_TOO_DISTANT"
    ACCOUNT_OUT_OF_SCOPE = "ACCOUNT_OUT_OF_SCOPE"


class FollowUpResponseOutcome(StrEnum):
    NO_RESPONSE_OBSERVED = "NO_RESPONSE_OBSERVED"
    REQUESTED_FOLLOW_UP = "REQUESTED_FOLLOW_UP"
    DEFERRED = "DEFERRED"
    NOT_CURRENT_PRIORITY = "NOT_CURRENT_PRIORITY"
    EXTERNAL_HELP_NOT_ACCEPTED = "EXTERNAL_HELP_NOT_ACCEPTED"
    REQUESTED_NO_CONTACT = "REQUESTED_NO_CONTACT"
    STAKEHOLDER_REFERRAL = "STAKEHOLDER_REFERRAL"
    UNCLASSIFIED_EVIDENCE = "UNCLASSIFIED_EVIDENCE"


@dataclass(frozen=True)
class StoppingRuleState:
    stopped: bool = False
    reason: StopReason | None = None

    def __post_init__(self) -> None:
        if self.stopped != (self.reason is not None):
            raise ValueError("A stopped state requires a reason and an active state cannot have one.")


@dataclass(frozen=True)
class FollowUpAction:
    """A simulated continuation with traceable context and no delivery capability."""

    id: str
    account: Account
    stakeholder: Stakeholder
    prior_interaction: OutreachAttempt | Conversation
    reason: FollowUpReason | None
    evidence_context: tuple[str, ...]
    proposed_message: str
    intended_timing: date
    status: FollowUpStatus = FollowUpStatus.PLANNED
    stopping_rule: StoppingRuleState = StoppingRuleState()
    attempt_count: int = 0
    requested_date: date | None = None
    requested_event: str = ""
    requested_event_observed: bool = False
    actual_message_sent: bool = False

    def __post_init__(self) -> None:
        if self.account.id != self.stakeholder.account_id:
            raise ValueError("Follow-up account and stakeholder must match.")
        if self.attempt_count < 0:
            raise ValueError("Follow-up attempt count cannot be negative.")
        if self.actual_message_sent:
            raise ValueError("This educational laboratory cannot send external communication.")
        if self.status is FollowUpStatus.CLOSED and not self.stopping_rule.stopped:
            raise ValueError("A closed follow-up requires a stopping rule state.")


@dataclass(frozen=True)
class StakeholderReferral:
    source_stakeholder_id: str
    referred_contact: Contact
    source_statement: StakeholderStatement
    interest_confirmed: bool = False

    def __post_init__(self) -> None:
        if self.source_statement.stakeholder_id != self.source_stakeholder_id:
            raise ValueError("Referral provenance must identify the referring stakeholder.")
        if self.referred_contact.account_id == "":
            raise ValueError("A referred contact must belong to an account.")
        if self.interest_confirmed:
            raise ValueError("A referral cannot establish the referred contact's interest.")
