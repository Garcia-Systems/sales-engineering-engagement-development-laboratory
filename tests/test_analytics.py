from dataclasses import FrozenInstanceError

import pytest

from engagement_dev.domain import (
    AnalyticsWarning,
    BottleneckKind,
    ClosureReason,
    ImprovementHypothesisStatus,
    PipelineState,
)
from engagement_dev.scenarios.chapter_fourteen import (
    analyze_chapter_fourteen,
    chapter_fourteen_report,
)
from engagement_dev.services.analytics import (
    ProcessAnalyzer,
    activity_produced_evidence,
)


def test_analytics_derive_from_existing_immutable_history():
    analysis = analyze_chapter_fourteen()
    before = analysis.history.pipeline_items[0].state_history
    ProcessAnalyzer().metrics(analysis.history)
    assert analysis.history.pipeline_items[0].state_history is before
    with pytest.raises(FrozenInstanceError):
        analysis.history.accounts_considered = 99


def test_counts_and_transitions_are_deterministic():
    first = analyze_chapter_fourteen().metrics
    second = analyze_chapter_fourteen().metrics
    assert first == second
    assert first.count("accounts_considered") == 20
    transitions = {
        (x.from_state, x.to_state): x.observed_count for x in first.transitions
    }
    assert transitions[(PipelineState.RESEARCHING, PipelineState.SIGNAL_FOUND)] == 1
    assert (
        transitions[
            (
                PipelineState.MORE_DISCOVERY_NEEDED,
                PipelineState.QUALIFIED_FOR_ENGAGEMENT,
            )
        ]
        == 1
    )


def test_time_in_state_is_deterministic_and_descriptive():
    durations = {x.state: x for x in analyze_chapter_fourteen().metrics.time_in_state}
    assert durations[PipelineState.RESEARCHING].average_scenario_days == 2.0
    assert durations[PipelineState.AWAITING_RESPONSE].average_scenario_days == 4.0


def test_activity_remains_distinct_from_evidence_production():
    analysis = analyze_chapter_fourteen()
    events = tuple(
        event for item in analysis.history.pipeline_items for event in item.activities
    )
    assert analysis.metrics.total_activities == len(events)
    assert analysis.metrics.evidence_producing_activities == sum(
        map(activity_produced_evidence, events)
    )
    assert (
        analysis.metrics.evidence_producing_activities
        < analysis.metrics.total_activities
    )


def test_closure_unknown_and_small_sample_remain_visible():
    metrics = analyze_chapter_fourteen().metrics
    closures = dict(metrics.closure_reasons)
    assert ClosureReason.UNKNOWN in closures
    assert closures[ClosureReason.UNKNOWN] == 1
    assert AnalyticsWarning.DESCRIPTIVE_ONLY in metrics.warnings
    assert AnalyticsWarning.INSUFFICIENT_SAMPLE in metrics.warnings


def test_bottleneck_references_evidence_without_a_causal_claim():
    finding = analyze_chapter_fourteen().retrospective.primary_bottleneck
    assert finding.kind is BottleneckKind.OUTREACH_RESPONSE_BOTTLENECK
    assert finding.evidence
    assert finding.causal_explanation == "UNKNOWN"
    assert "deserves investigation" in finding.interpretation


def test_hypothesis_experiment_and_plan_preserve_learning_limits():
    retrospective = analyze_chapter_fourteen().retrospective
    assert (
        retrospective.improvement_hypothesis.status
        is ImprovementHypothesisStatus.UNVALIDATED
    )
    experiment = retrospective.improvement_plan.experiments[0]
    assert experiment.interpretation_limits
    assert any(
        "does not establish causation" in item
        for item in experiment.interpretation_limits
    )
    assert len(retrospective.improvement_plan.changed_variables) <= 2


def test_market_comparison_is_scoped_and_no_prediction_is_created():
    analysis = analyze_chapter_fourteen()
    report = chapter_fourteen_report()
    assert analysis.metrics.market_counts
    assert "does not universally rank markets" in report
    assert (
        "Response rate is an observed scenario association, not causal proof" in report
    )
    assert analysis.metrics.revenue_forecast is None
    assert analysis.metrics.closed_deals is None
    assert "close probability" not in report.casefold()
    assert "REVENUE FORECAST\n\nNot modeled." in report


def test_cli_report_is_deterministic():
    assert chapter_fourteen_report() == chapter_fourteen_report()
    assert chapter_fourteen_report().startswith(
        "CHAPTER 14 — ENGAGEMENT DEVELOPMENT ANALYTICS"
    )
