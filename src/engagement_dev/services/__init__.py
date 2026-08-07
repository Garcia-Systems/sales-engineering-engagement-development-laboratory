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
