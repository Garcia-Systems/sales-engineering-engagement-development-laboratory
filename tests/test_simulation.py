from dataclasses import replace

import pytest

from engagement_dev.domain import (
    EngagementCandidate, OpportunityHypothesis, PipelineDisposition, PipelineState,
)
from engagement_dev.simulation import (
    EngagementDevelopmentSimulator, SimulationConfig, SimulationInvariantChecker,
    SimulationInvariantError, SimulationScenario, chapter_fifteen_report,
)


def run(scenario=SimulationScenario.PRODUCTIVE):
    config = SimulationConfig(scenario)
    if scenario is SimulationScenario.CAPACITY_CONSTRAINED:
        config = replace(config, research_capacity=2, conversation_capacity=1)
    return EngagementDevelopmentSimulator(config).run()


def test_productive_cycle_branches_and_uses_chapter_ten_handoff():
    result = run()
    assert result.successful
    assert result.item("Blue Heron Resort").engagement_candidate is not None
    assert result.handoffs[0].account.name == "Blue Heron Resort"
    assert result.item("Colonial Harbor Hotel").state_history[-1].state is PipelineState.CLOSED_NO_OPPORTUNITY
    assert result.item("Tidewater Inn").state_history[-1].state is PipelineState.MORE_DISCOVERY_NEEDED
    assert result.item("Peninsula Industrial Controls").engagement_candidate is None


def test_zero_engagement_is_success_and_has_no_handoff():
    result = run(SimulationScenario.ZERO_ENGAGEMENT)
    assert result.successful and result.handoffs == ()
    assert "The process worked because it prevented false opportunities." in chapter_fifteen_report("zero-engagement")


def test_capacity_constraint_creates_evidence_backed_deferrals():
    result = run(SimulationScenario.CAPACITY_CONSTRAINED)
    deferred = [x for x in result.pipeline_items if x.disposition is PipelineDisposition.DEFERRED]
    assert len(deferred) >= 3
    assert all(item.disposition_evidence for item in deferred)


def test_event_and_evidence_ledgers_are_deterministic_and_preserve_provenance():
    assert run() == run()
    result = run()
    assert all(event.source_subsystem.startswith("Chapter") for event in result.events)
    assert any(ledger.public_evidence for ledger in result.evidence_ledgers)
    assert result.metrics.count("engagement_candidates") == 1
    assert result.improvement_plan.status == "UNVALIDATED"


def test_invariants_reject_unsupported_hypothesis_and_fabricated_candidate():
    result = run()
    item = result.pipeline_items[1]
    bad_hypothesis = OpportunityHypothesis("bad", item.account.id, "Unsupported claim", ())
    bad = replace(item, hypothesis=bad_hypothesis)
    with pytest.raises(SimulationInvariantError, match="unsupported hypotheses"):
        SimulationInvariantChecker().check(replace(result, pipeline_items=(bad,) + result.pipeline_items[1:]))
    candidate = EngagementCandidate("bad-candidate", item.account.id, "bad", "missing")
    bad = replace(item, engagement_candidate=candidate)
    with pytest.raises(SimulationInvariantError, match="Candidates require qualification"):
        SimulationInvariantChecker().check(replace(result, pipeline_items=(bad,) + result.pipeline_items[1:]))


def test_cli_report_is_deterministic_and_has_no_forecast_or_probability():
    first = chapter_fifteen_report("productive")
    assert first == chapter_fifteen_report("productive")
    assert "REVENUE FORECAST\nNot modeled." in first
    assert "fake close probability" in first.casefold()
