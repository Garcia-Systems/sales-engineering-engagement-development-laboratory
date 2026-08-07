"""Policies that prevent desire from being mistaken for evidence."""

from collections.abc import Iterable
from dataclasses import dataclass
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
