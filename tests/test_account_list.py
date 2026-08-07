from engagement_dev.cli import main
from engagement_dev.domain import Account, AccountEvidence, AccountInterpretation, EvidenceCategory
from engagement_dev.scenarios import (
    build_chapter_three_queue, chapter_one_report, chapter_three_report,
    chapter_two_report, chapter_zero_report, load_chapter_three,
)
from engagement_dev.services import AccountListBuilder, AccountSelectionStatus


def _by_id():
    return {item.account_id: item for item in build_chapter_three_queue().evaluations}


def test_market_membership_alone_is_insufficient_and_explicit():
    result = _by_id()["heritage"]
    assert result.status is AccountSelectionStatus.INSUFFICIENT_EVIDENCE
    assert result.candidate is None


def test_account_evidence_retains_provenance_and_differs_from_interpretation():
    data = load_chapter_three()
    evidence = next(item for item in data.evidence if item.id == "br-1")
    interpretation = next(item for item in data.interpretations if item.id == "i-br")
    assert evidence.source == "Fictional company website — properties page"
    assert evidence.description != interpretation.statement
    assert interpretation.evidence_ids == ("br-1", "br-2", "br-3", "br-4")


def test_candidates_reference_selected_market_without_opportunity_semantics():
    result = _by_id()["blue-resort"]
    assert result.candidate is not None
    assert result.candidate.selected_market == load_chapter_three().selected_market
    assert result.candidate.relevant_problem_class_ids
    assert not hasattr(result.candidate, "opportunity_hypothesis")
    assert not hasattr(result.candidate, "engagement_candidate")


def test_outside_market_is_rejected_appropriately():
    assert _by_id()["peninsula-controls"].status is AccountSelectionStatus.OUTSIDE_SELECTED_MARKET


def test_absence_of_evidence_differs_from_negative_evidence():
    results = _by_id()
    assert results["sandpiper"].status is AccountSelectionStatus.INSUFFICIENT_EVIDENCE
    assert not results["sandpiper"].has_negative_evidence
    assert results["harborview"].status is AccountSelectionStatus.DEFERRED
    assert results["harborview"].has_negative_evidence


def test_capacity_limits_selection_and_deferred_is_not_rejected():
    queue = build_chapter_three_queue()
    assert len(queue.selected) == queue.capacity == 3
    results = _by_id()
    assert results["tidewater-inn"].status is AccountSelectionStatus.DEFERRED
    assert results["tidewater-inn"].candidate is not None


def test_order_and_tie_breaking_are_deterministic():
    assert build_chapter_three_queue() == build_chapter_three_queue()
    assert tuple(item.account_id for item in build_chapter_three_queue().selected) == (
        "blue-resort", "seaside-suites", "colonial-hotel",
    )


def test_builder_does_not_promote_inference_to_evidence():
    data = load_chapter_three()
    account = Account("inference-only", "Inference Only", "hospitality")
    evidence = (
        AccountEvidence("x1", account.id, "May use systems", EvidenceCategory.INFERENCE, "Analyst"),
        AccountEvidence("x2", account.id, "Might have handoffs", EvidenceCategory.INFERENCE, "Analyst"),
    )
    interpretations = (AccountInterpretation("ix", account.id, "Worth guessing about.", ("x1", "x2")),)
    queue = AccountListBuilder().build(
        selected_market=data.selected_market, supported_offer=data.supported_offer,
        market_characteristics=data.market_characteristics, accounts=(account,), evidence=evidence,
        interpretations=interpretations, research_capacity=1,
    )
    assert queue.evaluations[0].status is AccountSelectionStatus.INSUFFICIENT_EVIDENCE


def test_observed_account_fit_outside_offer_is_explicit():
    data = load_chapter_three()
    account = Account("specialist", "Specialist", "hospitality")
    evidence = (
        AccountEvidence("s1", account.id, "Publishes audit services", EvidenceCategory.PUBLIC_FACT, "Fictional page", ("SECURITY_AUDIT",)),
        AccountEvidence("s2", account.id, "Lists audit tooling", EvidenceCategory.PUBLIC_FACT, "Fictional catalog", ("SECURITY_AUDIT",)),
    )
    queue = AccountListBuilder().build(
        selected_market=data.selected_market, supported_offer=data.supported_offer,
        market_characteristics=data.market_characteristics, accounts=(account,), evidence=evidence,
        interpretations=(), research_capacity=1,
    )
    assert queue.evaluations[0].status is AccountSelectionStatus.OUTSIDE_SUPPORTED_OFFER


def test_chapters_zero_through_three_remain_deterministic(capsys):
    reports = (chapter_zero_report, chapter_one_report, chapter_two_report, chapter_three_report)
    assert all(report() == report() for report in reports)
    assert main(["chapter-3"]) == 0
    first = capsys.readouterr().out
    assert main(["chapter-3"]) == 0
    assert capsys.readouterr().out == first == chapter_three_report()
    assert "Qualified opportunities: 0" in first
    assert "Selected for deep research: 3" in first
