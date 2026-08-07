from dataclasses import fields, replace

import pytest

from engagement_dev.cli import main
from engagement_dev.domain import (
    AssumptionStatus, EvidenceFreshness, HypothesisStatus, UnknownCategory,
    UnsupportedHypothesisError,
)
from engagement_dev.scenarios import analyze_chapter_six, chapter_six_report
from engagement_dev.services import (
    HypothesisEvaluationOutcome, OpportunityHypothesisBuilder,
    OpportunityHypothesisEvaluator,
)


def test_supported_hypothesis_is_traceable_and_still_provisional():
    analysis = analyze_chapter_six()
    hypothesis = analysis.candidates[0].hypothesis
    assert hypothesis.status is HypothesisStatus.SUPPORTED_FOR_VALIDATION
    assert hypothesis.status is not HypothesisStatus.VALIDATED
    assert hypothesis.supporting_signal_ids
    assert {link.evidence_id for link in hypothesis.evidence_chain} == set(hypothesis.evidence_ids)
    assert {link.signal_id for link in hypothesis.evidence_chain} == set(hypothesis.supporting_signal_ids)


def test_assumptions_and_unknowns_cannot_silently_become_evidence():
    hypothesis = analyze_chapter_six().candidates[0].hypothesis
    assert all(item.status is AssumptionStatus.UNVALIDATED for item in hypothesis.assumptions)
    assert not set(item.id for item in hypothesis.assumptions) & set(hypothesis.evidence_ids)
    assert {item.category for item in hypothesis.unknowns} >= {
        UnknownCategory.PROBLEM_EXISTENCE, UnknownCategory.BUSINESS_IMPACT,
        UnknownCategory.STAKEHOLDER, UnknownCategory.BUDGET,
    }


def test_candidate_outcomes_reject_solution_first_and_unsupported_certainty():
    candidates = {item.label: item for item in analyze_chapter_six().candidates}
    assert candidates["A"].evaluation.outcome is HypothesisEvaluationOutcome.SUPPORTED_FOR_VALIDATION
    assert candidates["B"].evaluation.outcome is HypothesisEvaluationOutcome.SOLUTION_PREMATURE
    assert candidates["C"].evaluation.outcome is HypothesisEvaluationOutcome.INSUFFICIENT_EVIDENCE


def test_supported_signals_unknowns_problem_class_and_falsifiability_are_required():
    analysis = analyze_chapter_six()
    original = analysis.candidates[0].hypothesis
    kwargs = dict(
        identifier="invalid", account=analysis.chapter_five.brief.account,
        statement=original.cautious_statement, cluster=analysis.chapter_five.cluster,
        supporting_signals=(), relevant_problem_class_ids=original.relevant_problem_class_ids,
        reasoning=original.reasoning, assumptions=original.assumptions,
        unknowns=original.unknowns, falsification_conditions=original.falsification_conditions,
        validation_questions=original.validation_questions,
    )
    with pytest.raises(UnsupportedHypothesisError):
        OpportunityHypothesisBuilder().build(**kwargs)
    with pytest.raises(UnsupportedHypothesisError):
        OpportunityHypothesisBuilder().build(**(kwargs | {"supporting_signals": analysis.chapter_five.cluster.signals, "unknowns": ()}))
    with pytest.raises(UnsupportedHypothesisError):
        OpportunityHypothesisBuilder().build(**(kwargs | {"supporting_signals": analysis.chapter_five.cluster.signals, "relevant_problem_class_ids": ("UNSUPPORTED",)}))


def test_stale_only_evidence_and_outside_offer_do_not_receive_normal_support():
    analysis = analyze_chapter_six()
    draft = replace(analysis.candidates[0].hypothesis, status=HypothesisStatus.DRAFT)
    stale = tuple(replace(item, freshness=EvidenceFreshness.STALE) for item in analysis.chapter_five.cluster.signals)
    _, stale_result = OpportunityHypothesisEvaluator().evaluate(
        draft, signals=stale,
        supported_problem_class_ids=analysis.chapter_five.brief.relevant_problem_class_ids,
    )
    assert stale_result.outcome is HypothesisEvaluationOutcome.INSUFFICIENT_EVIDENCE
    outside = replace(draft, relevant_problem_class_ids=("UNSUPPORTED",))
    _, outside_result = OpportunityHypothesisEvaluator().evaluate(
        outside, signals=analysis.chapter_five.cluster.signals,
        supported_problem_class_ids=analysis.chapter_five.brief.relevant_problem_class_ids,
    )
    assert outside_result.outcome is HypothesisEvaluationOutcome.OUTSIDE_SUPPORTED_OFFER


def test_competing_hypotheses_coexist_and_preserve_falsification_paths():
    analysis = analyze_chapter_six()
    first, competing = analysis.candidates[0], analysis.candidates[3]
    assert first.hypothesis.competing_group_id == competing.hypothesis.competing_group_id
    assert first.evaluation.outcome is competing.evaluation.outcome is HypothesisEvaluationOutcome.SUPPORTED_FOR_VALIDATION
    assert first.evaluation.falsification_paths == first.hypothesis.falsification_conditions


def test_validation_questions_are_neutral_and_no_sales_fields_are_introduced():
    hypothesis = analyze_chapter_six().candidates[0].hypothesis
    assert any("working particularly well" in item for item in hypothesis.validation_questions)
    assert all("confirm that" not in item.casefold() for item in hypothesis.validation_questions)
    names = {item.name for item in fields(type(hypothesis))}
    assert not names & {"deal_value", "purchase_probability", "engagement_candidate"}
    assert "CONFIRMED CUSTOMER PROBLEMS\n0" in chapter_six_report()
    assert "QUALIFIED ENGAGEMENTS\n0" in chapter_six_report()


def test_unrelated_signals_remain_rejected_by_chapter_five_cluster_invariant():
    # Chapter 6 accepts only members of the already validated Chapter 5 cluster.
    analysis = analyze_chapter_six()
    outsider = analysis.chapter_five.candidates[-1]
    original = analysis.candidates[0].hypothesis
    with pytest.raises(UnsupportedHypothesisError):
        OpportunityHypothesisBuilder().build(
            identifier="unrelated", account=analysis.chapter_five.brief.account,
            statement=original.cautious_statement, cluster=analysis.chapter_five.cluster,
            supporting_signals=(outsider,), relevant_problem_class_ids=("SYSTEM_INTEGRATION",),
            reasoning="Artificial combination", assumptions=original.assumptions,
            unknowns=original.unknowns, falsification_conditions=original.falsification_conditions,
            validation_questions=original.validation_questions,
        )


def test_chapter_six_cli_is_deterministic_and_prior_chapters_still_run(capsys):
    assert chapter_six_report() == chapter_six_report()
    for chapter in range(7):
        assert main([f"chapter-{chapter}"]) == 0
        capsys.readouterr()
    assert main(["chapter-6"]) == 0
    first = capsys.readouterr().out
    assert main(["chapter-6"]) == 0
    assert capsys.readouterr().out == first == chapter_six_report()
