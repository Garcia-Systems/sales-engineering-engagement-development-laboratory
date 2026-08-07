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
)


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
