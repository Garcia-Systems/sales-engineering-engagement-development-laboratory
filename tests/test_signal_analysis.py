from dataclasses import replace

import pytest

from engagement_dev.cli import main
from engagement_dev.domain import (
    EvidenceFreshness,
    SignalCluster,
    SignalPolarity,
    SignalStrength,
    SignalType,
)
from engagement_dev.scenarios import (
    analyze_chapter_five,
    chapter_five_report,
    chapter_four_report,
    chapter_one_report,
    chapter_three_report,
    chapter_two_report,
    chapter_zero_report,
)
from engagement_dev.services import SignalEvaluationStatus, SignalEvaluator


def test_signals_require_supporting_evidence_and_type_is_deterministic():
    analysis = analyze_chapter_five()
    assert analysis.candidates[0].signal_type is SignalType.EXPANSION
    assert all(item.supporting_evidence for item in analysis.candidates)
    unsupported = replace(analysis.candidates[0], supporting_evidence=())
    result = SignalEvaluator().evaluate(
        unsupported, analysis.brief.relevant_problem_class_ids
    )
    assert result.status is SignalEvaluationStatus.INSUFFICIENT_EVIDENCE
    with pytest.raises(ValueError):
        replace(analysis.candidates[0], source="")


def test_observation_interpretation_unknowns_and_strength_semantics_are_separate():
    evaluation = analyze_chapter_five().evaluations[0]
    assert (
        evaluation.signal.description
        != evaluation.signal.interpretation.possible_meaning
    )
    assert evaluation.signal.interpretation.unresolved_questions
    assert evaluation.strength is SignalStrength.MODERATE
    assert not hasattr(evaluation, "purchase_probability")


def test_stale_and_generic_observations_are_rejected():
    results = {item.signal.id: item for item in analyze_chapter_five().evaluations}
    assert results["signal-manual-history"].signal.freshness is EvidenceFreshness.STALE
    assert (
        results["signal-manual-history"].status is SignalEvaluationStatus.STALE_SIGNAL
    )
    assert (
        results["signal-generic"].status is SignalEvaluationStatus.INSUFFICIENT_EVIDENCE
    )


def test_duplicate_reports_are_one_event_but_independent_events_corroborate():
    analysis = analyze_chapter_five()
    expansion = analysis.evaluations[0]
    assert len(expansion.signal.supporting_evidence) == 4
    assert expansion.independent_event_ids == ("event-fourth-property",)
    assert analysis.underlying_expansion_events == 1
    assert analysis.cluster.strength is SignalStrength.STRONG
    assert len({item.underlying_event_id for item in analysis.cluster.signals}) == 3


def test_unrelated_signals_cannot_be_clustered():
    analysis = analyze_chapter_five()
    unrelated = replace(
        analysis.candidates[1],
        interpretation=replace(
            analysis.candidates[1].interpretation,
            relevant_problem_class_ids=("UNRELATED",),
        ),
    )
    with pytest.raises(ValueError):
        SignalCluster(
            "bad",
            analysis.brief.account.id,
            "Artificial",
            (analysis.candidates[0], unrelated),
            ("SYSTEM_INTEGRATION",),
            "Not justified",
            ("Why?",),
            SignalStrength.STRONG,
        )


def test_negative_signal_weakens_but_does_not_eliminate_research():
    platform = analyze_chapter_five().evaluations[2]
    assert platform.signal.polarity is SignalPolarity.NEGATIVE
    assert platform.status is SignalEvaluationStatus.SIGNAL_SUPPORTED
    assert "weaken" in platform.weakened_interpretation


def test_analysis_creates_neither_problem_hypothesis_nor_engagement_candidate():
    analysis = analyze_chapter_five()
    assert not hasattr(analysis, "opportunity_hypothesis")
    assert not hasattr(analysis, "engagement_candidate")
    assert "Opportunity hypotheses validated: 0" in chapter_five_report()


def test_chapters_zero_through_five_and_cli_output_remain_deterministic(capsys):
    reports = (
        chapter_zero_report,
        chapter_one_report,
        chapter_two_report,
        chapter_three_report,
        chapter_four_report,
        chapter_five_report,
    )
    assert all(report() == report() for report in reports)
    for chapter in range(6):
        assert main([f"chapter-{chapter}"]) == 0
        capsys.readouterr()
    assert main(["chapter-5"]) == 0
    first = capsys.readouterr().out
    assert main(["chapter-5"]) == 0
    assert capsys.readouterr().out == first == chapter_five_report()
    assert "Supported signals: 3" in first
    assert "Rejected observations: 2" in first
