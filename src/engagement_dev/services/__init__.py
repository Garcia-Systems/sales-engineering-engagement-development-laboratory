"""Policies that prevent desire from being mistaken for evidence."""

from collections.abc import Iterable
from dataclasses import dataclass, replace
from enum import StrEnum

from engagement_dev.domain import (
    Account,
    CapabilityProfile,
    EngagementCandidate,
    ObservedSignal,
    OpportunityHypothesis,
    QualificationAssessment,
    UnqualifiedEngagementError,
    UnsupportedHypothesisError,
    ServiceOffer,
    Market,
    MarketCharacteristic,
    MarketEvidence,
    MarketHypothesis,
    AccountEvidence,
    AccountInterpretation,
    AccountCandidate,
    AccountResearchBrief,
    EvidenceFreshness,
    ResearchDimension,
    SourceReliability,
    PublicSourceType,
    SignalCluster,
    SignalPolarity,
    SignalStrength,
    Assumption,
    EvidenceChainLink,
    HypothesisStatus,
    HypothesisUnknown,
    AuthorityStatus,
    EvidenceProximity,
    KnowledgeDomain,
    OrganizationalRole,
    QuestionProximity,
    RelationshipType,
    Stakeholder,
    StakeholderEvidence,
    StakeholderMap,
    StakeholderRelationship,
    ValidationQuestionMapping,
    OutreachAttempt, OutreachChannel, OutreachMessage, OutreachObjective, OutreachStatus,
    Conversation, ConversationEvidence, ConversationObjective, ConversationQuestion, ConversationStage,
    ConversationStatus, HypothesisOutcome, QuestionType, StatementRelationship,
    StakeholderStatement,
    ExternalHelpState, ImpactState, KnowledgeState, OwnershipState, PriorityState,
    ProblemState, ProviderFitState, QualificationDimension, QualificationDimensionName,
    QualificationOutcome, TimingState,
)

from datetime import date


def create_hypothesis(
    *, hypothesis_id: str, account: Account, statement: str, evidence: Iterable[ObservedSignal]
) -> OpportunityHypothesis:
    """Create a hypothesis only from direct evidence belonging to this account."""
    supporting = tuple(
        signal for signal in evidence if signal.account_id == account.id and signal.is_direct_evidence
    )
    if not supporting:
        raise UnsupportedHypothesisError(
            f"No direct evidence supports a hypothesis for {account.name}."
        )
    return OpportunityHypothesis(
        id=hypothesis_id,
        account_id=account.id,
        cautious_statement=statement,
        evidence_ids=tuple(signal.id for signal in supporting),
    )


def create_engagement_candidate(
    *, candidate_id: str, account: Account, hypothesis: OpportunityHypothesis,
    qualification: QualificationAssessment
) -> EngagementCandidate:
    """Cross the laboratory boundary only after an explicit positive assessment."""
    if (
        not qualification.condition_met
        or (qualification.outcome is not None and qualification.outcome is not QualificationOutcome.QUALIFIED_FOR_ENGAGEMENT)
        or qualification.hypothesis_id != hypothesis.id
        or hypothesis.account_id != account.id
        or not qualification.evidence_ids
    ):
        raise UnqualifiedEngagementError("Explicit, evidence-backed qualification is required.")
    return EngagementCandidate(
        id=candidate_id,
        account_id=account.id,
        hypothesis_id=hypothesis.id,
        qualification_id=qualification.id,
        account=account,
        validated_problem_hypothesis=hypothesis,
        qualification_assessment=qualification,
    )


class QualificationEvaluator:
    """A conservative ordered threshold: evidence, never a score, crosses the boundary."""

    required_names = frozenset(QualificationDimensionName)

    def evaluate(
        self, *, assessment_id: str, opportunity_hypothesis: OpportunityHypothesis,
        refined_hypothesis: OpportunityHypothesis, dimensions: tuple[QualificationDimension, ...],
        unresolved_gaps: tuple[str, ...] = (), contradictions: tuple[str, ...] = (),
    ) -> QualificationAssessment:
        by_name = {item.name: item for item in dimensions}
        missing = self.required_names - by_name.keys()
        if missing:
            raise ValueError("Qualification must explicitly represent every dimension: " + ", ".join(sorted(item.value for item in missing)))

        def state(name: QualificationDimensionName):
            return by_name[name].state

        if state(QualificationDimensionName.PROBLEM) is ProblemState.REFUTED:
            outcome = QualificationOutcome.NO_CURRENT_OPPORTUNITY
        elif state(QualificationDimensionName.PRIORITY) in {PriorityState.LOW, PriorityState.NOT_A_PRIORITY}:
            outcome = QualificationOutcome.NOT_CURRENT_PRIORITY
        elif state(QualificationDimensionName.EXTERNAL_HELP) in {ExternalHelpState.INTERNAL_ONLY, ExternalHelpState.NOT_INTERESTED}:
            outcome = QualificationOutcome.EXTERNAL_HELP_NOT_ACCEPTED
        elif state(QualificationDimensionName.IMPACT) is ImpactState.NO_ACTIONABLE_IMPACT:
            outcome = QualificationOutcome.NO_ACTIONABLE_IMPACT
        elif state(QualificationDimensionName.OWNERSHIP) is OwnershipState.UNKNOWN:
            outcome = QualificationOutcome.NO_CLEAR_OWNER
        elif state(QualificationDimensionName.TIMING) is TimingState.DEFERRED:
            outcome = QualificationOutcome.TIMING_NOT_ACTIVE
        elif state(QualificationDimensionName.PROVIDER_FIT) is not ProviderFitState.SUPPORTED:
            outcome = QualificationOutcome.NOT_A_FIT if state(QualificationDimensionName.PROVIDER_FIT) is ProviderFitState.NOT_A_FIT else QualificationOutcome.MORE_DISCOVERY_NEEDED
        else:
            passes = (
                state(QualificationDimensionName.PROBLEM) is ProblemState.CONFIRMED
                and state(QualificationDimensionName.IMPACT) is ImpactState.CONFIRMED
                and state(QualificationDimensionName.PRIORITY) in {PriorityState.ACTIVE, PriorityState.EMERGING}
                and state(QualificationDimensionName.OWNERSHIP) is OwnershipState.IDENTIFIED
                and state(QualificationDimensionName.TIMING) in {TimingState.ACTIVE, TimingState.UPCOMING}
                and state(QualificationDimensionName.PROVIDER_FIT) is ProviderFitState.SUPPORTED
                and state(QualificationDimensionName.EXTERNAL_HELP) in {ExternalHelpState.OPEN, ExternalHelpState.POSSIBLY_OPEN}
                and state(QualificationDimensionName.AGREED_INVESTIGATION) is KnowledgeState.KNOWN
            )
            outcome = QualificationOutcome.QUALIFIED_FOR_ENGAGEMENT if passes else QualificationOutcome.MORE_DISCOVERY_NEEDED

        evidence_ids = tuple(dict.fromkeys(identifier for item in dimensions for identifier in item.evidence_ids))
        qualified = outcome is QualificationOutcome.QUALIFIED_FOR_ENGAGEMENT
        explanation = (
            "There is customer-grounded evidence of a specific problem, meaningful operational impact, active priority, ownership, relevant timing, provider fit, and willingness to consider deeper investigation."
            if qualified else f"The evidence produces {outcome.value}; the engagement threshold is not satisfied."
        )
        return QualificationAssessment(
            assessment_id, refined_hypothesis.id, qualified, explanation, evidence_ids,
            opportunity_hypothesis, refined_hypothesis, dimensions, unresolved_gaps,
            contradictions, outcome, explanation,
            "Begin a structured Sales Engineering engagement." if qualified else "Resolve evidence gaps or defer without assuming an opportunity.",
        )


class OfferEvaluationStatus(StrEnum):
    SUPPORTED = "SUPPORTED"
    INSUFFICIENT_PROOF = "INSUFFICIENT_PROOF"
    NO_PROBLEM_CLASS = "NO_PROBLEM_CLASS"
    OUTSIDE_CAPABILITY = "OUTSIDE_CAPABILITY"
    OVERCLAIMED = "OVERCLAIMED"


@dataclass(frozen=True)
class OfferEvaluation:
    status: OfferEvaluationStatus
    findings: tuple[str, ...]
    relevant_capability_ids: tuple[str, ...]
    supporting_proof_ids: tuple[str, ...]


class OfferEvaluator:
    """Apply explicit, ordered grounding rules; no opaque sales score is used."""

    _overclaim_terms = ("guarantee", "guaranteed", "revolutionize any", "will cut")

    def evaluate(self, offer: ServiceOffer, profile: CapabilityProfile) -> OfferEvaluation:
        capability_ids = frozenset(cap.identifier for cap in profile.capabilities)
        proof_by_id = {proof.identifier: proof for proof in profile.proof_artifacts}
        selected = tuple(dict.fromkeys(offer.capability_ids))
        proof_ids = tuple(
            proof_id
            for proof_id in offer.proof_artifact_ids
            if proof_id in proof_by_id
            and capability_ids.intersection(proof_by_id[proof_id].capability_ids)
        )
        statement = offer.statement.casefold()

        if any(term in statement for term in self._overclaim_terms):
            return OfferEvaluation(
                OfferEvaluationStatus.OVERCLAIMED,
                (
                    "The statement promises or generalizes an outcome that discovery has not established.",
                    "No customer investigation has occurred.",
                ),
                selected,
                proof_ids,
            )
        outside = tuple(identifier for identifier in selected if identifier not in capability_ids)
        if outside:
            return OfferEvaluation(
                OfferEvaluationStatus.OUTSIDE_CAPABILITY,
                tuple(f"Capability {identifier!r} is not in the provider profile." for identifier in outside),
                selected,
                proof_ids,
            )
        if not offer.problem_classes:
            return OfferEvaluation(
                OfferEvaluationStatus.NO_PROBLEM_CLASS,
                ("The statement does not identify a recognizable problem class.",),
                selected,
                proof_ids,
            )
        uncovered = tuple(
            problem.identifier
            for problem in offer.problem_classes
            if not set(problem.relevant_capability_ids).intersection(selected)
        )
        if uncovered:
            return OfferEvaluation(
                OfferEvaluationStatus.OUTSIDE_CAPABILITY,
                tuple(f"Problem class {identifier} has no relevant selected capability." for identifier in uncovered),
                selected,
                proof_ids,
            )
        supported_capabilities = {
            capability_id
            for proof_id in proof_ids
            for capability_id in proof_by_id[proof_id].capability_ids
        }
        unsupported = tuple(identifier for identifier in selected if identifier not in supported_capabilities)
        if unsupported:
            return OfferEvaluation(
                OfferEvaluationStatus.INSUFFICIENT_PROOF,
                tuple(f"Capability {identifier!r} has no selected supporting proof." for identifier in unsupported),
                selected,
                proof_ids,
            )
        return OfferEvaluation(
            OfferEvaluationStatus.SUPPORTED,
            (
                "Every problem class has a relevant demonstrated capability.",
                "The offer remains an investigation, not a claim of customer need or guaranteed outcome.",
            ),
            selected,
            proof_ids,
        )


class InvestigationPriority(StrEnum):
    PRIORITIZE_FOR_RESEARCH = "PRIORITIZE_FOR_RESEARCH"
    WORTH_INVESTIGATING = "WORTH_INVESTIGATING"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    OUTSIDE_SUPPORTED_OFFER = "OUTSIDE_SUPPORTED_OFFER"


@dataclass(frozen=True)
class MarketEvaluation:
    market_id: str
    priority: InvestigationPriority
    relevant_problem_class_ids: tuple[str, ...]
    supporting_evidence_ids: tuple[str, ...]
    findings: tuple[str, ...]
    hypothesis: MarketHypothesis | None


@dataclass(frozen=True)
class ResearchCycle:
    capacity: int
    selected_market_ids: tuple[str, ...]
    deferred_market_ids: tuple[str, ...]
    rejected_market_ids: tuple[str, ...]
    insufficient_evidence_market_ids: tuple[str, ...]


class MarketEvaluator:
    """Explain whether market-level evidence merits scarce account-research attention."""

    def evaluate(
        self,
        *,
        supported_offer: ServiceOffer,
        profile: CapabilityProfile,
        market: Market,
        characteristics: tuple[MarketCharacteristic, ...],
        evidence: tuple[MarketEvidence, ...],
        excluded_boundary_ids: tuple[str, ...] = (),
    ) -> MarketEvaluation:
        # This is intentionally a short rule sequence rather than a lead score.
        if excluded_boundary_ids:
            statements = {item.identifier: item.statement for item in profile.boundaries}
            boundaries = tuple(statements[item] for item in excluded_boundary_ids if item in statements)
            return MarketEvaluation(
                market.id, InvestigationPriority.OUTSIDE_SUPPORTED_OFFER, (), (),
                tuple(f"Provider boundary applies: {statement}" for statement in boundaries), None,
            )

        offer_problem_ids = {problem.identifier for problem in supported_offer.problem_classes}
        market_characteristics = tuple(item for item in characteristics if item.market_id == market.id)
        evidence_by_id = {item.id: item for item in evidence if item.market_id == market.id}
        relevant = tuple(dict.fromkeys(
            problem_id
            for characteristic in market_characteristics
            for problem_id in characteristic.relevant_problem_class_ids
            if problem_id in offer_problem_ids
        ))
        supporting = tuple(dict.fromkeys(
            evidence_id
            for characteristic in market_characteristics
            if set(characteristic.relevant_problem_class_ids).intersection(relevant)
            for evidence_id in characteristic.evidence_ids
            if evidence_id in evidence_by_id and evidence_by_id[evidence_id].is_observed
        ))
        if not relevant or not supporting:
            return MarketEvaluation(
                market.id, InvestigationPriority.INSUFFICIENT_EVIDENCE, relevant, supporting,
                ("Observed evidence does not yet support account-level research for a supported problem class.",), None,
            )

        priority = (
            InvestigationPriority.PRIORITIZE_FOR_RESEARCH
            if len(relevant) >= 2 and len(supporting) >= 2
            else InvestigationPriority.WORTH_INVESTIGATING
        )
        hypothesis = MarketHypothesis(
            f"hypothesis-{market.id}", market.id,
            f"{market.name} may be worth investigating for {', '.join(relevant).lower()} opportunities.",
            relevant, supporting,
            ("Market patterns may not apply to any individual organization.",),
            "Observed characteristics overlap with problem classes in the supported offer.",
        )
        return MarketEvaluation(
            market.id, priority, relevant, supporting,
            (
                "Market characteristics overlap with supported problem classes.",
                "This research priority is not proof of account need or a sales forecast.",
            ), hypothesis,
        )

    def allocate(self, evaluations: tuple[MarketEvaluation, ...], capacity: int) -> ResearchCycle:
        if capacity < 0:
            raise ValueError("Research capacity cannot be negative.")
        eligible = tuple(item for item in evaluations if item.priority in (
            InvestigationPriority.PRIORITIZE_FOR_RESEARCH,
            InvestigationPriority.WORTH_INVESTIGATING,
        ))
        selected = eligible[:capacity]
        return ResearchCycle(
            capacity,
            tuple(item.market_id for item in selected),
            tuple(item.market_id for item in eligible[capacity:]),
            tuple(item.market_id for item in evaluations if item.priority is InvestigationPriority.OUTSIDE_SUPPORTED_OFFER),
            tuple(item.market_id for item in evaluations if item.priority is InvestigationPriority.INSUFFICIENT_EVIDENCE),
        )


class AccountSelectionStatus(StrEnum):
    SELECTED_FOR_RESEARCH = "SELECTED_FOR_RESEARCH"
    DEFERRED = "DEFERRED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    OUTSIDE_SELECTED_MARKET = "OUTSIDE_SELECTED_MARKET"
    OUTSIDE_SUPPORTED_OFFER = "OUTSIDE_SUPPORTED_OFFER"


class AccountPriority(StrEnum):
    RECENT_CHANGE_AND_COMPLEXITY = "RECENT_CHANGE_AND_COMPLEXITY"
    MULTIPLE_RELEVANT_CHARACTERISTICS = "MULTIPLE_RELEVANT_CHARACTERISTICS"
    SUFFICIENT_PUBLIC_INFORMATION = "SUFFICIENT_PUBLIC_INFORMATION"


@dataclass(frozen=True)
class AccountEvaluation:
    account_id: str
    status: AccountSelectionStatus
    reason: str
    candidate: AccountCandidate | None
    interpretations: tuple[AccountInterpretation, ...]
    priority: AccountPriority | None
    has_negative_evidence: bool


@dataclass(frozen=True)
class AccountResearchQueue:
    capacity: int
    evaluations: tuple[AccountEvaluation, ...]

    @property
    def selected(self) -> tuple[AccountEvaluation, ...]:
        return tuple(item for item in self.evaluations if item.status is AccountSelectionStatus.SELECTED_FOR_RESEARCH)


class AccountListBuilder:
    """Build an explainable research queue using ordered rules, never a lead score."""

    def build(
        self, *, selected_market: Market, supported_offer: ServiceOffer,
        market_characteristics: tuple[MarketCharacteristic, ...], accounts: tuple[Account, ...],
        evidence: tuple[AccountEvidence, ...], interpretations: tuple[AccountInterpretation, ...],
        research_capacity: int,
    ) -> AccountResearchQueue:
        if research_capacity < 0:
            raise ValueError("Research capacity cannot be negative.")
        offer_problems = {item.identifier for item in supported_offer.problem_classes}
        characteristics = tuple(item for item in market_characteristics if item.market_id == selected_market.id)
        provisional: list[AccountEvaluation] = []
        eligible: list[tuple[int, str, AccountEvaluation]] = []
        priority_order = {
            AccountPriority.RECENT_CHANGE_AND_COMPLEXITY: 0,
            AccountPriority.MULTIPLE_RELEVANT_CHARACTERISTICS: 1,
            AccountPriority.SUFFICIENT_PUBLIC_INFORMATION: 2,
        }
        for account in accounts:
            account_evidence = tuple(item for item in evidence if item.account_id == account.id and item.is_observed)
            account_interpretations = tuple(item for item in interpretations if item.account_id == account.id)
            if account.market_id != selected_market.id:
                provisional.append(AccountEvaluation(
                    account.id, AccountSelectionStatus.OUTSIDE_SELECTED_MARKET,
                    "The organization is outside the selected market.", None, account_interpretations, None, False,
                ))
                continue
            relevant = tuple(dict.fromkeys(
                problem for item in account_evidence for problem in item.relevant_problem_class_ids
                if problem in offer_problems
            ))
            described_problems = tuple(dict.fromkeys(
                problem for item in account_evidence for problem in item.relevant_problem_class_ids
            ))
            negative = any(item.is_negative for item in account_evidence)
            supporting = tuple(item for item in account_evidence if set(item.relevant_problem_class_ids).intersection(relevant))
            if negative:
                provisional.append(AccountEvaluation(
                    account.id, AccountSelectionStatus.DEFERRED,
                    "Negative evidence suggests the current investigation is not appropriate; revisit only if circumstances change.",
                    None, account_interpretations, None, True,
                ))
                continue
            if described_problems and not relevant:
                provisional.append(AccountEvaluation(
                    account.id, AccountSelectionStatus.OUTSIDE_SUPPORTED_OFFER,
                    "Observed characteristics relate only to problem classes outside the supported offer.",
                    None, account_interpretations, None, False,
                ))
                continue
            if len(supporting) < 2 or not relevant:
                provisional.append(AccountEvaluation(
                    account.id, AccountSelectionStatus.INSUFFICIENT_EVIDENCE,
                    "Market membership alone does not justify deeper account research.", None,
                    account_interpretations, None, False,
                ))
                continue
            candidate = AccountCandidate(
                account, selected_market, supporting, characteristics, relevant,
                "Observable operational characteristics overlap with supported problem classes and justify more research; no customer problem is established.",
            )
            recent = any("recent" in item.description.casefold() or "expansion" in item.description.casefold() for item in supporting)
            if recent and len(supporting) >= 3:
                priority = AccountPriority.RECENT_CHANGE_AND_COMPLEXITY
            elif len(supporting) >= 3 or len(relevant) >= 2:
                priority = AccountPriority.MULTIPLE_RELEVANT_CHARACTERISTICS
            else:
                priority = AccountPriority.SUFFICIENT_PUBLIC_INFORMATION
            evaluation = AccountEvaluation(
                account.id, AccountSelectionStatus.DEFERRED,
                "Relevant evidence supports research, subject to limited research capacity.",
                candidate, account_interpretations, priority, False,
            )
            provisional.append(evaluation)
            eligible.append((priority_order[priority], account.name.casefold(), evaluation))

        selected_ids = {item.account_id for _, _, item in sorted(eligible)[:research_capacity]}
        final = tuple(
            AccountEvaluation(
                item.account_id, AccountSelectionStatus.SELECTED_FOR_RESEARCH,
                "Selected within current research capacity using explicit priority and alphabetical tie-breaking.",
                item.candidate, item.interpretations, item.priority, item.has_negative_evidence,
            ) if item.account_id in selected_ids else item
            for item in provisional
        )
        # The queue is ordered by selected priority first; all other outcomes retain input order.
        selected = sorted(
            (item for item in final if item.status is AccountSelectionStatus.SELECTED_FOR_RESEARCH),
            key=lambda item: (priority_order[item.priority], item.candidate.account.name.casefold()),  # type: ignore[index,union-attr]
        )
        return AccountResearchQueue(research_capacity, tuple(selected) + tuple(
            item for item in final if item.status is not AccountSelectionStatus.SELECTED_FOR_RESEARCH
        ))


class ResearchReadinessStatus(StrEnum):
    RESEARCH_READY = "RESEARCH_READY"
    MORE_RESEARCH_NEEDED = "MORE_RESEARCH_NEEDED"
    INSUFFICIENT_PUBLIC_EVIDENCE = "INSUFFICIENT_PUBLIC_EVIDENCE"
    CONFLICT_REQUIRES_REVIEW = "CONFLICT_REQUIRES_REVIEW"


@dataclass(frozen=True)
class ResearchReadinessResult:
    status: ResearchReadinessStatus
    reasons: tuple[str, ...]
    stop_broad_research: bool


def classify_freshness(observed_on: date, research_date: date) -> EvidenceFreshness:
    """Current <= 90 days, aging <= 365 days, otherwise stale."""
    age = (research_date - observed_on).days
    if age < 0:
        raise ValueError("Evidence cannot be dated after the scenario research date.")
    if age <= 90:
        return EvidenceFreshness.CURRENT
    if age <= 365:
        return EvidenceFreshness.AGING
    return EvidenceFreshness.STALE


def classify_source_reliability(source_type: PublicSourceType) -> SourceReliability:
    """Apply the scenario's explicit categorical provenance policy."""
    if source_type in {
        PublicSourceType.COMPANY_WEBSITE,
        PublicSourceType.PUBLIC_JOB_POSTING,
        PublicSourceType.PRESS_RELEASE,
        PublicSourceType.PUBLIC_VENDOR_PAGE,
    }:
        return SourceReliability.PRIMARY_PUBLIC_SOURCE
    if source_type in {PublicSourceType.PUBLIC_NEWS_ARTICLE, PublicSourceType.PUBLIC_DIRECTORY}:
        return SourceReliability.SECONDARY_PUBLIC_SOURCE
    return SourceReliability.UNVERIFIED_PUBLIC_CLAIM


class AccountResearchEvaluator:
    """Evaluate research sufficiency, never opportunity or engagement merit."""

    def evaluate(self, brief: AccountResearchBrief) -> ResearchReadinessResult:
        if any(item.requires_review for item in brief.conflicts):
            return ResearchReadinessResult(
                ResearchReadinessStatus.CONFLICT_REQUIRES_REVIEW,
                ("Contradictory evidence must be interpreted explicitly before signal analysis.",), False,
            )
        sourced = tuple(item for item in brief.evidence if item.source and item.source_type and item.source_reliability)
        if len(sourced) < 2:
            return ResearchReadinessResult(
                ResearchReadinessStatus.INSUFFICIENT_PUBLIC_EVIDENCE,
                ("At least two public evidence records with provenance are required.",), False,
            )
        dimensions = {item.dimension for item in sourced}
        missing = []
        if ResearchDimension.ORGANIZATION not in dimensions:
            missing.append("Basic organization evidence is missing.")
        if ResearchDimension.OPERATIONS not in dimensions:
            missing.append("No operational workflow has been observed.")
        if not brief.unknowns:
            missing.append("Important unknowns have not been recorded.")
        if missing:
            return ResearchReadinessResult(ResearchReadinessStatus.MORE_RESEARCH_NEEDED, tuple(missing), False)
        return ResearchReadinessResult(
            ResearchReadinessStatus.RESEARCH_READY,
            (
                "Organization understood sufficiently",
                "Operational workflows identified",
                "Evidence provenance preserved",
                "Important unknowns explicitly recorded",
            ), True,
        )


class SignalEvaluationStatus(StrEnum):
    SIGNAL_SUPPORTED = "SIGNAL_SUPPORTED"
    SIGNAL_WEAK = "SIGNAL_WEAK"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    STALE_SIGNAL = "STALE_SIGNAL"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"
    OUTSIDE_SUPPORTED_OFFER = "OUTSIDE_SUPPORTED_OFFER"


@dataclass(frozen=True)
class SignalEvaluation:
    signal: ObservedSignal
    status: SignalEvaluationStatus
    strength: SignalStrength
    reasons: tuple[str, ...]
    independent_event_ids: tuple[str, ...]
    weakened_interpretation: str = ""


class SignalEvaluator:
    """Explain whether evidence justifies questions, without predicting a purchase."""

    _generic_phrases = ("committed to innovation", "digital transformation")

    def evaluate(
        self, signal: ObservedSignal, supported_problem_class_ids: tuple[str, ...]
    ) -> SignalEvaluation:
        interpretation = signal.interpretation
        events = tuple(
            dict.fromkeys(
                (signal.underlying_event_id or item.id)
                for item in signal.supporting_evidence
            )
        )
        if not signal.supporting_evidence or not signal.is_direct_evidence:
            return SignalEvaluation(
                signal,
                SignalEvaluationStatus.INSUFFICIENT_EVIDENCE,
                SignalStrength.WEAK,
                ("No direct account-research evidence supports this observation.",),
                events,
            )
        if any(
            phrase in signal.description.casefold() for phrase in self._generic_phrases
        ):
            return SignalEvaluation(
                signal,
                SignalEvaluationStatus.INSUFFICIENT_EVIDENCE,
                SignalStrength.WEAK,
                (
                    "Generic marketing language provides no specific operational observation.",
                ),
                events,
            )
        if signal.freshness is EvidenceFreshness.STALE:
            return SignalEvaluation(
                signal,
                SignalEvaluationStatus.STALE_SIGNAL,
                SignalStrength.WEAK,
                (
                    "The event may remain historically true, but its investigative relevance has decayed.",
                ),
                events,
            )
        relevant = set(
            interpretation.relevant_problem_class_ids if interpretation else ()
        )
        overlap = relevant.intersection(supported_problem_class_ids)
        if not overlap:
            return SignalEvaluation(
                signal,
                SignalEvaluationStatus.OUTSIDE_SUPPORTED_OFFER,
                SignalStrength.WEAK,
                (
                    "The observation has no explicit connection to a supported problem class.",
                ),
                events,
            )
        weakened = ""
        if signal.polarity is SignalPolarity.NEGATIVE:
            weakened = "New evidence may weaken or make an earlier interpretation obsolete; stakeholder validation is still required."
        return SignalEvaluation(
            signal,
            SignalEvaluationStatus.SIGNAL_SUPPORTED,
            SignalStrength.MODERATE,
            (
                "Current, specific evidence connects cautiously to a supported problem class.",
                "Substantial uncertainty remains; no customer problem or purchase intent is established.",
            ),
            events,
            weakened,
        )

    def build_cluster(
        self,
        *,
        identifier: str,
        account_id: str,
        theme: str,
        evaluations: tuple[SignalEvaluation, ...],
        interpretation: str,
        questions: tuple[str, ...],
    ) -> SignalCluster:
        supported = tuple(
            item.signal
            for item in evaluations
            if item.status is SignalEvaluationStatus.SIGNAL_SUPPORTED
        )
        event_ids = {signal.underlying_event_id or signal.id for signal in supported}
        problem_sets = [
            set(signal.interpretation.relevant_problem_class_ids)
            for signal in supported
            if signal.interpretation
        ]
        shared = set.intersection(*problem_sets) if problem_sets else set()
        strength = (
            SignalStrength.STRONG if len(event_ids) >= 2 else SignalStrength.MODERATE
        )
        return SignalCluster(
            identifier,
            account_id,
            theme,
            supported,
            tuple(sorted(shared)),
            interpretation,
            questions,
            strength,
        )


class HypothesisEvaluationOutcome(StrEnum):
    SUPPORTED_FOR_VALIDATION = "SUPPORTED_FOR_VALIDATION"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    TOO_BROAD = "TOO_BROAD"
    SOLUTION_PREMATURE = "SOLUTION_PREMATURE"
    CONTRADICTED_BY_EVIDENCE = "CONTRADICTED_BY_EVIDENCE"
    OUTSIDE_SUPPORTED_OFFER = "OUTSIDE_SUPPORTED_OFFER"


@dataclass(frozen=True)
class OpportunityHypothesisEvaluation:
    outcome: HypothesisEvaluationOutcome
    findings: tuple[str, ...]
    supporting_evidence_ids: tuple[str, ...]
    assumptions: tuple[Assumption, ...]
    unanswered_questions: tuple[HypothesisUnknown, ...]
    falsification_paths: tuple[str, ...]


class OpportunityHypothesisBuilder:
    """Build a traceable draft while keeping evidence, assumptions, and unknowns separate."""

    def build(
        self, *, identifier: str, account: Account, statement: str,
        cluster: SignalCluster, supporting_signals: tuple[ObservedSignal, ...],
        relevant_problem_class_ids: tuple[str, ...], reasoning: str,
        assumptions: tuple[Assumption, ...], unknowns: tuple[HypothesisUnknown, ...],
        falsification_conditions: tuple[str, ...], validation_questions: tuple[str, ...],
        competing_group_id: str = "",
    ) -> OpportunityHypothesis:
        if cluster.account_id != account.id or any(s.account_id != account.id for s in supporting_signals):
            raise UnsupportedHypothesisError("The account, cluster, and signals must refer to one account.")
        cluster_ids = {item.id for item in cluster.signals}
        if not supporting_signals or not {item.id for item in supporting_signals} <= cluster_ids:
            raise UnsupportedHypothesisError("At least one supported signal from the cluster is required.")
        evidence = tuple(dict.fromkeys(
            item.id for signal in supporting_signals for item in signal.supporting_evidence
            if item.is_observed
        ))
        if not evidence:
            raise UnsupportedHypothesisError("Traceable observed evidence is required.")
        if not relevant_problem_class_ids or not set(relevant_problem_class_ids) <= set(cluster.relevant_problem_class_ids):
            raise UnsupportedHypothesisError("A relevant cluster-supported problem class is required.")
        if not unknowns:
            raise UnsupportedHypothesisError("Important unknowns must be explicit.")
        if not falsification_conditions:
            raise UnsupportedHypothesisError("A hypothesis must be falsifiable.")
        chain = tuple(
            EvidenceChainLink(item.id, signal.id)
            for signal in supporting_signals for item in signal.supporting_evidence
            if item.is_observed
        )
        return OpportunityHypothesis(
            identifier, account.id, statement, evidence,
            tuple(item.id for item in supporting_signals), cluster.id,
            relevant_problem_class_ids, reasoning, assumptions, unknowns,
            falsification_conditions, validation_questions, chain,
            HypothesisStatus.DRAFT, competing_group_id,
        )


class OpportunityHypothesisEvaluator:
    """Apply explainable epistemic rules without probabilities or sales scoring."""

    _solution_nouns = ("api", "platform", "software", "integration platform", "custom solution")
    _prescriptive = ("needs", "must buy", "should implement", "requires our")
    _certainty = ("definitely", "guaranteed", "will fail", "clearly needs", "systems are broken", "is failing")
    _cautious = (" may ", " might ", " could ", "potentially", "investigating whether")
    _customer_intent = ("wants to buy", "wants our", "is ready to buy", "will hire us", "seeks external help")

    def evaluate(
        self, hypothesis: OpportunityHypothesis, *, signals: tuple[ObservedSignal, ...],
        supported_problem_class_ids: tuple[str, ...], contradictory_evidence_ids: tuple[str, ...] = (),
    ) -> tuple[OpportunityHypothesis, OpportunityHypothesisEvaluation]:
        statement = f" {hypothesis.cautious_statement.casefold()} "
        findings: tuple[str, ...]
        has_stakeholder_evidence = any(
            evidence.category.value == "STAKEHOLDER_STATEMENT"
            for signal in signals for evidence in signal.supporting_evidence
        )
        if any(term in statement for term in self._customer_intent) and not has_stakeholder_evidence:
            outcome = HypothesisEvaluationOutcome.INSUFFICIENT_EVIDENCE
            findings = ("Customer intent cannot be claimed without stakeholder evidence.",)
        elif any(term in statement for term in self._prescriptive) and any(noun in statement for noun in self._solution_nouns):
            outcome = HypothesisEvaluationOutcome.SOLUTION_PREMATURE
            findings = ("The statement prescribes a technical solution before the business problem is validated.",)
        elif any(term in statement for term in self._certainty):
            outcome = HypothesisEvaluationOutcome.INSUFFICIENT_EVIDENCE
            findings = ("The statement asserts certainty or failure that the evidence does not establish.",)
        elif not any(term in statement for term in self._cautious):
            outcome = HypothesisEvaluationOutcome.TOO_BROAD
            findings = ("The statement is not framed as a cautious, testable possible problem.",)
        elif not set(hypothesis.relevant_problem_class_ids) <= set(supported_problem_class_ids):
            outcome = HypothesisEvaluationOutcome.OUTSIDE_SUPPORTED_OFFER
            findings = ("The proposed problem class is outside the supported offer.",)
        elif set(hypothesis.evidence_ids).intersection(contradictory_evidence_ids):
            outcome = HypothesisEvaluationOutcome.CONTRADICTED_BY_EVIDENCE
            findings = ("Explicit contradictory evidence prevents normal support.",)
        else:
            by_id = {item.id: item for item in signals}
            selected = tuple(by_id[item] for item in hypothesis.supporting_signal_ids if item in by_id)
            if (not selected or all(item.freshness is EvidenceFreshness.STALE for item in selected)
                    or not hypothesis.evidence_ids):
                outcome = HypothesisEvaluationOutcome.INSUFFICIENT_EVIDENCE
                findings = ("Current traceable signal evidence is required.",)
            else:
                outcome = HypothesisEvaluationOutcome.SUPPORTED_FOR_VALIDATION
                findings = (
                    "Evidence supports testing this explanation with stakeholders.",
                    "Support for validation is provisional and does not mean validated.",
                )
        status = {
            HypothesisEvaluationOutcome.SUPPORTED_FOR_VALIDATION: HypothesisStatus.SUPPORTED_FOR_VALIDATION,
            HypothesisEvaluationOutcome.CONTRADICTED_BY_EVIDENCE: HypothesisStatus.CONTRADICTED,
        }.get(outcome, HypothesisStatus.INSUFFICIENT_EVIDENCE)
        evaluated = replace(hypothesis, status=status)
        return evaluated, OpportunityHypothesisEvaluation(
            outcome, findings, hypothesis.evidence_ids, hypothesis.assumptions,
            hypothesis.unknowns, hypothesis.falsification_conditions,
        )


class DomainCoverage(StrEnum):
    COVERED = "COVERED"
    UNKNOWN = "UNKNOWN"


class CoverageStatus(StrEnum):
    COVERAGE_READY = "COVERAGE_READY"
    PARTIAL_COVERAGE = "PARTIAL_COVERAGE"
    IMPORTANT_GAPS = "IMPORTANT_GAPS"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


@dataclass(frozen=True)
class ValidationCoverage:
    by_domain: tuple[tuple[KnowledgeDomain, DomainCoverage], ...]
    status: CoverageStatus
    rationale: str


class ContactPriority(StrEnum):
    """Priority for learning, explicitly not likelihood of purchase."""

    PRIMARY_VALIDATION_CONTACT = "PRIMARY_VALIDATION_CONTACT"
    SECONDARY_VALIDATION_CONTACT = "SECONDARY_VALIDATION_CONTACT"
    LATER_STAGE_CONTACT = "LATER_STAGE_CONTACT"
    INSUFFICIENT_RELEVANCE = "INSUFFICIENT_RELEVANCE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ContactPriorityDecision:
    stakeholder_id: str
    priority: ContactPriority
    rationale: str


class StakeholderMapper:
    """Construct and evaluate an evidence map without inferring buyer status."""

    def build(
        self, *, account_id: str, hypothesis_id: str,
        stakeholders: tuple[Stakeholder, ...],
        relationships: tuple[StakeholderRelationship, ...],
        question_mappings: tuple[ValidationQuestionMapping, ...],
    ) -> StakeholderMap:
        ids = {item.contact.id for item in stakeholders}
        evidence_ids = {evidence.id for item in stakeholders for evidence in item.evidence}
        if any(item.account_id != account_id for item in stakeholders):
            raise ValueError("All stakeholders must belong to the mapped account.")
        if any(item.source_contact_id not in ids or item.target_contact_id not in ids for item in relationships):
            raise ValueError("Relationships may reference only mapped contacts.")
        if any(not set(item.evidence_ids) <= evidence_ids for item in relationships):
            raise ValueError("Relationship provenance must be present in stakeholder evidence.")
        if any(not set(item.stakeholder_ids) <= ids for item in question_mappings):
            raise ValueError("Question mappings may reference only mapped stakeholders.")
        return StakeholderMap(account_id, hypothesis_id, stakeholders, relationships, question_mappings)

    def evaluate_coverage(
        self, stakeholder_map: StakeholderMap,
        domains: tuple[KnowledgeDomain, ...],
    ) -> ValidationCoverage:
        mapped = {domain for item in stakeholder_map.stakeholders for domain in item.knowledge_domains}
        coverage = tuple(
            (domain, DomainCoverage.COVERED if domain in mapped else DomainCoverage.UNKNOWN)
            for domain in domains
        )
        foundational = {KnowledgeDomain.WORKFLOW, KnowledgeDomain.TECHNOLOGY, KnowledgeDomain.BUSINESS_IMPACT}
        covered = {domain for domain, status in coverage if status is DomainCoverage.COVERED}
        if foundational <= covered:
            status = CoverageStatus.COVERAGE_READY
            rationale = "Core hypothesis domains have plausible evidence sources; finance and procurement may remain unknown for an initial conversation."
        elif covered & foundational:
            status = CoverageStatus.PARTIAL_COVERAGE
            rationale = "Some core evidence domains have plausible sources, but important perspectives are missing."
        elif covered:
            status = CoverageStatus.IMPORTANT_GAPS
            rationale = "Mapped knowledge does not cover the core validation questions."
        else:
            status = CoverageStatus.INSUFFICIENT_EVIDENCE
            rationale = "No supported stakeholder knowledge covers the requested domains."
        return ValidationCoverage(coverage, status, rationale)

    def prioritize(self, stakeholder_map: StakeholderMap) -> tuple[ContactPriorityDecision, ...]:
        mapped_questions = {item.question for item in stakeholder_map.question_mappings if item.stakeholder_ids}
        ranked: list[tuple[int, int, Stakeholder]] = []
        weights = {EvidenceProximity.DIRECT: 3, EvidenceProximity.NEAR: 2, EvidenceProximity.INDIRECT: 1, EvidenceProximity.UNKNOWN: 0}
        for order, stakeholder in enumerate(stakeholder_map.stakeholders):
            relevant = tuple(item for item in stakeholder.question_proximities if item.validation_question in mapped_questions)
            score = sum(weights[item.proximity] for item in relevant)
            ranked.append((-score, order, stakeholder))
        ranked.sort(key=lambda item: (item[0], item[1]))
        positive = [item for item in ranked if item[0] < 0]
        primary_id = positive[0][2].contact.id if positive else ""
        decisions = []
        for negative_score, _, stakeholder in ranked:
            score = -negative_score
            if stakeholder.contact.id == primary_id:
                priority = ContactPriority.PRIMARY_VALIDATION_CONTACT
                rationale = "Supported responsibilities and direct question-specific proximity make this person the closest source for current validation evidence."
            elif score >= 2:
                priority = ContactPriority.SECONDARY_VALIDATION_CONTACT
                rationale = "This person can add a supported perspective to current validation questions."
            elif score == 1:
                priority = ContactPriority.LATER_STAGE_CONTACT
                rationale = "This person's supported knowledge is less direct for the current questions."
            else:
                priority = ContactPriority.UNKNOWN
                rationale = "Current evidence does not establish proximity to a mapped validation question."
            decisions.append(ContactPriorityDecision(stakeholder.contact.id, priority, rationale))
        return tuple(decisions)


class OutreachEvaluationOutcome(StrEnum):
    SUPPORTED = "SUPPORTED"
    UNSUPPORTED_CLAIM = "UNSUPPORTED_CLAIM"
    REJECTED_ASSUMPTIONS = "REJECTED_ASSUMPTIONS"
    INSUFFICIENT_RELEVANCE = "INSUFFICIENT_RELEVANCE"
    SOLUTION_PREMATURE = "SOLUTION_PREMATURE"
    TOO_BROAD = "TOO_BROAD"
    CTA_TOO_AGGRESSIVE = "CTA_TOO_AGGRESSIVE"


@dataclass(frozen=True)
class OutreachEvaluation:
    outcome: OutreachEvaluationOutcome
    findings: tuple[str, ...]


class OutreachEvaluator:
    """Ordered, explainable outreach rules; no score and no sending capability."""

    _assumptions = ("must be causing", "systems are broken", "losing money", "definitely have", "serious integration problems")
    _solutions = ("build an api", "build software", "fix your systems", "implement our", "our solution")
    _aggressive_ctas = ("schedule a demo", "send you a proposal", "when can we start", "who controls the budget", "sign up")
    _fabricated_proof = ("our customers", "case study", "certified", "partner", "saved clients", "guaranteed")

    def evaluate(
        self, message: OutreachMessage, *, account_evidence_ids: tuple[str, ...],
        stakeholder: Stakeholder, proof_artifact_ids: tuple[str, ...], max_words: int | None = None,
    ) -> OutreachEvaluation:
        text = message.body.casefold()
        cited = {item for claim in message.factual_claims for item in claim.evidence_ids}
        available_public_evidence = set(account_evidence_ids) | {item.id for item in stakeholder.evidence}
        if any(not claim.evidence_ids for claim in message.factual_claims) or not cited <= available_public_evidence:
            return OutreachEvaluation(OutreachEvaluationOutcome.UNSUPPORTED_CLAIM, ("Every factual account or stakeholder claim must cite available public evidence.",))
        if any(term in text for term in self._fabricated_proof) or not set(message.credibility_proof_ids) <= set(proof_artifact_ids):
            return OutreachEvaluation(OutreachEvaluationOutcome.UNSUPPORTED_CLAIM, ("Credibility and social proof must trace to Chapter 1 proof artifacts.",))
        if any(term in text for term in self._assumptions) or (message.validation_question and not message.validation_question.strip().endswith("?")):
            return OutreachEvaluation(OutreachEvaluationOutcome.REJECTED_ASSUMPTIONS, ("The message converts an internal hypothesis into an unsupported customer claim.",))
        if any(term in text for term in self._solutions):
            return OutreachEvaluation(OutreachEvaluationOutcome.SOLUTION_PREMATURE, ("The message proposes a solution before the hypothesis is validated.",))
        if any(term in message.call_to_action.casefold() for term in self._aggressive_ctas):
            return OutreachEvaluation(OutreachEvaluationOutcome.CTA_TOO_AGGRESSIVE, ("The call to action asks for commitment rather than a conversation.",))
        stakeholder_supported = stakeholder.contact.id == message.stakeholder_id and bool(stakeholder.question_proximities)
        if not message.factual_claims or not message.relevance.strip() or not stakeholder_supported:
            return OutreachEvaluation(OutreachEvaluationOutcome.INSUFFICIENT_RELEVANCE, ("The message does not explain evidence-based organization, topic, and recipient relevance.",))
        limit = max_words or (90 if message.channel is OutreachChannel.PROFESSIONAL_NETWORK else 150)
        if len(message.body.split()) > limit:
            return OutreachEvaluation(OutreachEvaluationOutcome.TOO_BROAD, ("The message contains more context and capability detail than this channel needs.",))
        if message.objective is not OutreachObjective.VALIDATE_HYPOTHESIS:
            return OutreachEvaluation(OutreachEvaluationOutcome.INSUFFICIENT_RELEVANCE, ("The message is not designed to validate the current hypothesis.",))
        return OutreachEvaluation(OutreachEvaluationOutcome.SUPPORTED, (
            "Public claims trace to evidence.", "Recipient relevance is supported.",
            "The hypothesis remains a question.", "Credibility traces to Chapter 1 proof.",
            "The call to action asks only for a conversation.",
        ))

    def ready_attempt(self, message: OutreachMessage, evaluation: OutreachEvaluation) -> OutreachAttempt:
        status = OutreachStatus.READY if evaluation.outcome is OutreachEvaluationOutcome.SUPPORTED else OutreachStatus.DRAFT
        return OutreachAttempt(message, status)


class OutreachChannelAdapter:
    """Render the same supported components at deterministic channel lengths."""

    def render(self, message: OutreachMessage, channel: OutreachChannel) -> str:
        if channel is OutreachChannel.PROFESSIONAL_NETWORK:
            return " ".join((message.observation, message.relevance, message.validation_question, message.call_to_action))
        if channel is OutreachChannel.EMAIL:
            return " ".join((message.observation, message.relevance, message.credibility, message.validation_question, message.call_to_action))
        return "\n".join((f"OBSERVATION: {message.observation}", f"QUESTION: {message.validation_question}", f"NEXT STEP: {message.call_to_action}"))


class ConversationEvaluationOutcome(StrEnum):
    DISCOVERY_COMPLETE = "DISCOVERY_COMPLETE"
    MORE_DISCOVERY_NEEDED = "MORE_DISCOVERY_NEEDED"
    ASSUMPTION_LED = "ASSUMPTION_LED"
    PITCH_PREMATURE = "PITCH_PREMATURE"
    INSUFFICIENT_EVIDENCE_CAPTURE = "INSUFFICIENT_EVIDENCE_CAPTURE"


@dataclass(frozen=True)
class ConversationEvaluation:
    outcome: ConversationEvaluationOutcome
    findings: tuple[str, ...]


class ConversationEvaluator:
    """Explainable discovery checks; no score, forecast, or solution selection."""

    _loaded_terms = (
        "how bad", "how much money", "broken workflow", "broken system",
        "why haven't", "why haven’t", "who has the budget", "integration problems",
    )
    _pitch_terms = (
        "schedule a demo", "our solution", "build an integration", "send a proposal",
        "buy our", "implement our",
    )

    def is_neutral(self, question: ConversationQuestion | str) -> bool:
        text = question.text if isinstance(question, ConversationQuestion) else question
        folded = text.casefold()
        return text.strip().endswith("?") and not any(term in folded for term in self._loaded_terms)

    def select_follow_up(self, statement: StakeholderStatement) -> ConversationQuestion:
        """Follow the disclosed evidence instead of advancing a fixed questionnaire."""
        text = statement.statement.casefold()
        if "manually" in text or "manual" in text:
            prompt = "Which event details have to be transferred manually?"
        elif "separate" in text or "event booking" in text:
            prompt = "What information moves between the event workflow and property operations?"
        elif statement.relationship is StatementRelationship.CONTRADICTS:
            prompt = "What parts of the current process work particularly well?"
        else:
            prompt = "Could you say more about what happens in that workflow?"
        return ConversationQuestion(prompt, QuestionType.WORKFLOW, ConversationStage.CLARIFY)

    def evaluate(self, conversation: Conversation) -> ConversationEvaluation:
        text = " ".join(item.text for item in conversation.questions).casefold()
        if any(term in text for term in self._pitch_terms) or any(
            term in conversation.next_step.casefold() for term in self._pitch_terms
        ):
            return ConversationEvaluation(
                ConversationEvaluationOutcome.PITCH_PREMATURE,
                ("The conversation selected a pitch or solution before discovery established one.",),
            )
        if any(not self.is_neutral(item) for item in conversation.questions):
            return ConversationEvaluation(
                ConversationEvaluationOutcome.ASSUMPTION_LED,
                ("At least one question assumes pain, cost, or buying conditions.",),
            )
        captured = {item.statement for item in conversation.stakeholder_statements}
        evidence_statements = {item.statement.statement for item in conversation.evidence_captured}
        if not captured or captured != evidence_statements:
            return ConversationEvaluation(
                ConversationEvaluationOutcome.INSUFFICIENT_EVIDENCE_CAPTURE,
                ("Every stakeholder statement must remain traceable and separate from interpretation.",),
            )
        if conversation.objective is not ConversationObjective.VALIDATE_OPPORTUNITY_HYPOTHESIS:
            return ConversationEvaluation(
                ConversationEvaluationOutcome.ASSUMPTION_LED,
                ("The conversation is not aligned to hypothesis validation.",),
            )
        if not conversation.unresolved_questions:
            return ConversationEvaluation(
                ConversationEvaluationOutcome.INSUFFICIENT_EVIDENCE_CAPTURE,
                ("Discovery must preserve material unknowns.",),
            )
        if conversation.status is not ConversationStatus.COMPLETED:
            return ConversationEvaluation(
                ConversationEvaluationOutcome.MORE_DISCOVERY_NEEDED,
                ("The simulated conversation has not been completed.",),
            )
        return ConversationEvaluation(
            ConversationEvaluationOutcome.DISCOVERY_COMPLETE,
            (
                "The conversation reduced uncertainty with neutral, traceable evidence.",
                "A refutation is valid discovery; completion does not imply qualification.",
            ),
        )
