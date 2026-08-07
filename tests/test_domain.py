import pytest

from engagement_dev.domain import (
    Account, EvidenceCategory, ObservedSignal, QualificationAssessment,
    UnqualifiedEngagementError, UnsupportedHypothesisError,
)
from engagement_dev.services import create_engagement_candidate, create_hypothesis


ACCOUNT = Account("a1", "Example Account", "m1")
FACT = ObservedSignal("e1", "a1", "Published a migration notice", EvidenceCategory.PUBLIC_FACT, "notice")


def test_hypothesis_retains_evidence_references():
    hypothesis = create_hypothesis(hypothesis_id="h1", account=ACCOUNT, statement="Investigate migration risk.", evidence=(FACT,))
    assert hypothesis.evidence_ids == ("e1",)


def test_unsupported_hypothesis_is_rejected():
    with pytest.raises(UnsupportedHypothesisError):
        create_hypothesis(hypothesis_id="h1", account=ACCOUNT, statement="They need us.", evidence=())


def test_account_can_exist_without_opportunity():
    assert ACCOUNT.name == "Example Account"
    with pytest.raises(UnsupportedHypothesisError):
        create_hypothesis(hypothesis_id="h1", account=ACCOUNT, statement="Wishful thinking", evidence=())


def test_inference_is_not_observed_evidence():
    inference = ObservedSignal("i1", "a1", "They may be struggling", EvidenceCategory.INFERENCE, "analyst")
    assert not inference.is_direct_evidence
    with pytest.raises(UnsupportedHypothesisError):
        create_hypothesis(hypothesis_id="h1", account=ACCOUNT, statement="Investigate.", evidence=(inference,))


def test_candidate_requires_explicit_qualification():
    hypothesis = create_hypothesis(hypothesis_id="h1", account=ACCOUNT, statement="Investigate.", evidence=(FACT,))
    failed = QualificationAssessment("q1", "h1", False, "Authority not established", ("e1",))
    with pytest.raises(UnqualifiedEngagementError):
        create_engagement_candidate(candidate_id="c1", account=ACCOUNT, hypothesis=hypothesis, qualification=failed)
    passed = QualificationAssessment("q2", "h1", True, "Explicit condition confirmed", ("e1",))
    candidate = create_engagement_candidate(candidate_id="c1", account=ACCOUNT, hypothesis=hypothesis, qualification=passed)
    assert candidate.qualification_id == "q2"
