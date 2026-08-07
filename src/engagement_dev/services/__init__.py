"""Policies that prevent desire from being mistaken for evidence."""

from collections.abc import Iterable

from engagement_dev.domain import (
    Account,
    EngagementCandidate,
    ObservedSignal,
    OpportunityHypothesis,
    QualificationAssessment,
    UnqualifiedEngagementError,
    UnsupportedHypothesisError,
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
