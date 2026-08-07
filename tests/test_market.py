from engagement_dev.domain import Account, Market
from engagement_dev.cli import main
from engagement_dev.scenarios import (
    chapter_one_report, chapter_two_report, chapter_two_research_cycle,
    chapter_zero_report, evaluate_chapter_two, load_chapter_two,
)
from engagement_dev.services import InvestigationPriority, MarketEvaluator


def test_market_characteristics_do_not_create_accounts_or_opportunities():
    candidate = load_chapter_two().candidates[0]
    assert candidate.market.account_ids == ()
    assert candidate.characteristics
    assert not hasattr(candidate.market, "opportunities")


def test_market_extension_preserves_chapter_zero_constructor():
    market = Market("m", "Market", ("a",))
    account = Account("a", "Account", market.id)
    assert market.account_ids == (account.id,)
    assert market.description == ""


def test_hypotheses_retain_only_observed_evidence_references():
    results = {candidate.market.id: result for candidate, result in evaluate_chapter_two()}
    hypothesis = results["hospitality"].hypothesis
    assert hypothesis is not None
    assert hypothesis.evidence_ids == ("hospitality-e1", "hospitality-e2")
    assert hypothesis.assumptions == ("Market patterns may not apply to any individual organization.",)
    assert results["weak"].hypothesis is None


def test_weak_evidence_is_insufficient_and_boundary_rejects_market():
    results = {candidate.market.id: result for candidate, result in evaluate_chapter_two()}
    assert results["weak"].priority is InvestigationPriority.INSUFFICIENT_EVIDENCE
    assert results["industrial"].priority is InvestigationPriority.OUTSIDE_SUPPORTED_OFFER
    assert "industrial control engineering" in results["industrial"].findings[0].lower()


def test_supported_problem_classes_control_relevance():
    data = load_chapter_two()
    candidate = data.candidates[0]
    empty_offer = type(data.supported_offer)(
        "empty", "Bounded investigation.", data.supported_offer.capability_ids, (),
        data.supported_offer.proof_artifact_ids, data.supported_offer.boundaries,
    )
    result = MarketEvaluator().evaluate(
        supported_offer=empty_offer, profile=data.profile, market=candidate.market,
        characteristics=candidate.characteristics, evidence=candidate.evidence,
    )
    assert result.priority is InvestigationPriority.INSUFFICIENT_EVIDENCE
    assert result.relevant_problem_class_ids == ()


def test_evaluation_and_cli_are_deterministic_without_regressions():
    assert evaluate_chapter_two() == evaluate_chapter_two()
    assert chapter_two_report() == chapter_two_report()
    assert chapter_zero_report() == chapter_zero_report()
    assert chapter_one_report() == chapter_one_report()
    assert "PRIORITIZE_FOR_RESEARCH" in chapter_two_report()
    assert "OUTSIDE_SUPPORTED_OFFER" in chapter_two_report()
    assert "INSUFFICIENT_EVIDENCE" in chapter_two_report()


def test_capacity_defers_without_mutating_evidence_or_rejecting():
    data = load_chapter_two()
    evaluations = tuple(result for _, result in evaluate_chapter_two())
    before = data.candidates[2].evidence
    cycle = MarketEvaluator().allocate(evaluations, 2)
    assert cycle == chapter_two_research_cycle()
    assert cycle.selected_market_ids == ("hospitality", "retail")
    assert cycle.deferred_market_ids == ("professional",)
    assert cycle.rejected_market_ids == ("industrial",)
    assert cycle.insufficient_evidence_market_ids == ("weak",)
    assert load_chapter_two().candidates[2].evidence == before


def test_chapter_two_cli_output_is_deterministic(capsys):
    assert main(["chapter-2"]) == 0
    first = capsys.readouterr().out
    assert main(["chapter-2"]) == 0
    second = capsys.readouterr().out
    assert first == second == chapter_two_report()
