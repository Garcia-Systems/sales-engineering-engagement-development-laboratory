from dataclasses import FrozenInstanceError, replace
from datetime import date

import pytest

from engagement_dev.domain import (
    Account, ActivityEvent, ActivityType, HypothesisStatus, PipelineCapacity,
    PipelineDisposition, PipelineItem, PipelineState, PipelineWipLimits,
)
from engagement_dev.scenarios.chapter_twelve import TODAY, analyze_chapter_twelve, chapter_twelve_report
from engagement_dev.services import (
    PipelineCapacityPlanner, PipelineHealthFinding, PipelineProjector,
    derive_pipeline_state, next_justified_action, pipeline_health, stale_items,
)


def by_name(name):
    return next(item for item in analyze_chapter_twelve().items if item.account.name == name)


def test_state_is_derived_from_existing_lifecycle_evidence():
    analysis = analyze_chapter_twelve()
    assert {item.account.name: derive_pipeline_state(item) for item in analysis.items} == {
        "Tidewater Inn": PipelineState.RESEARCHING,
        "Colonial Harbor Hotel": PipelineState.HYPOTHESIS_SUPPORTED,
        "Blue Heron Resort": PipelineState.QUALIFIED_FOR_ENGAGEMENT,
        "Peninsula Home Services": PipelineState.AWAITING_RESPONSE,
        "Harbor Street Music": PipelineState.DEFERRED,
        "Heritage Lodging Group": PipelineState.CLOSED_NO_OPPORTUNITY,
        "Peninsula Industrial Controls": PipelineState.OUT_OF_SCOPE,
    }


def test_state_cannot_be_assigned_or_arbitrarily_promoted():
    item = by_name("Tidewater Inn")
    assert not hasattr(item, "stage") and not hasattr(item, "state")
    with pytest.raises(FrozenInstanceError):
        item.account = Account("fake", "Fake", "fake")
    assert derive_pipeline_state(replace(item, activities=(ActivityEvent(TODAY, ActivityType.NOTE_ADDED, "optimistic note"),))) is PipelineState.RESEARCHING


def test_activity_does_not_change_evidence_state():
    item = by_name("Peninsula Home Services")
    assert len(item.activities) == 6
    assert derive_pipeline_state(item) is PipelineState.AWAITING_RESPONSE
    assert len(item.state_history) == 1


def test_state_history_is_preserved():
    states = [event.state for event in by_name("Blue Heron Resort").state_history]
    assert states[0] is PipelineState.RESEARCHING
    assert states[-1] is PipelineState.QUALIFIED_FOR_ENGAGEMENT
    assert len(states) == 9


def test_new_evidence_can_regress_qualified_item_to_deferred():
    item = by_name("Blue Heron Resort")
    changed = replace(item, disposition=PipelineDisposition.DEFERRED, disposition_evidence="Project postponed indefinitely.")
    refreshed = PipelineProjector().refresh(changed, occurred_on=TODAY, evidence_event="Stakeholder postponed project.")
    assert derive_pipeline_state(refreshed) is PipelineState.DEFERRED
    assert refreshed.state_history[:-1] == item.state_history


def test_refuted_hypothesis_closes_without_alternate():
    item = by_name("Colonial Harbor Hotel")
    changed = replace(item, hypothesis=replace(item.hypothesis, status=HypothesisStatus.REFUTED))
    assert derive_pipeline_state(changed) is PipelineState.CLOSED_NO_OPPORTUNITY


def test_qualified_assessment_and_candidate_are_both_required():
    item = by_name("Blue Heron Resort")
    assert derive_pipeline_state(item) is PipelineState.QUALIFIED_FOR_ENGAGEMENT
    assert derive_pipeline_state(replace(item, engagement_candidate=None)) is PipelineState.MORE_DISCOVERY_NEEDED


def test_no_response_waits_and_consumes_no_capacity():
    item = by_name("Peninsula Home Services")
    action = next_justified_action(item)
    assert action.capacity_kind is None
    assert "Wait" in action.description


def test_deferred_item_does_not_consume_capacity():
    deferred = by_name("Harbor Street Music")
    allocation = PipelineCapacityPlanner().allocate((deferred,), PipelineCapacity())
    assert allocation.selected == ()


def test_capacity_allocation_is_deterministic_and_limited():
    researching = tuple(PipelineItem(Account(str(i), f"Account {i}", "market")) for i in range(3))
    planner = PipelineCapacityPlanner()
    first = planner.allocate(researching, PipelineCapacity(deep_research_slots=2))
    second = planner.allocate(researching, PipelineCapacity(deep_research_slots=2))
    assert first == second
    assert [name for name, _ in first.selected] == ["Account 0", "Account 1"]


def test_wip_limits_are_enforced_as_explainable_violations():
    researching = tuple(PipelineItem(Account(str(i), f"Account {i}", "market")) for i in range(4))
    result = PipelineCapacityPlanner().allocate(researching, PipelineCapacity(), PipelineWipLimits(deep_research=3))
    assert result.wip_violations == ("EXCESS_DEEP_RESEARCH_WIP",)


def test_next_actions_derive_from_state():
    assert next_justified_action(by_name("Tidewater Inn")).description == "Complete account research"
    assert next_justified_action(by_name("Colonial Harbor Hotel")).description == "Map stakeholders"
    assert next_justified_action(by_name("Heritage Lodging Group")).description == "None"


def test_stale_items_are_flagged_not_rejected():
    stale = stale_items(analyze_chapter_twelve().items, today=TODAY)
    assert [item.account.name for item in stale] == ["Harbor Street Music"]
    assert derive_pipeline_state(stale[0]) is PipelineState.DEFERRED


def test_health_findings_are_explainable_without_score():
    findings = pipeline_health(analyze_chapter_twelve().items, today=TODAY)
    assert findings[0].finding is PipelineHealthFinding.BALANCED_PIPELINE
    assert all(finding.explanation for finding in findings)
    assert not hasattr(findings[0], "score")


def test_no_financial_forecast_or_probability_is_modeled():
    analysis = analyze_chapter_twelve()
    assert analysis.projected_revenue is None
    assert not hasattr(analysis, "close_probability")
    assert "Not calculated." in chapter_twelve_report()


def test_closed_and_out_of_scope_remain_distinct():
    assert derive_pipeline_state(by_name("Heritage Lodging Group")) is PipelineState.CLOSED_NO_OPPORTUNITY
    assert derive_pipeline_state(by_name("Peninsula Industrial Controls")) is PipelineState.OUT_OF_SCOPE


def test_chapter_twelve_output_is_deterministic():
    assert chapter_twelve_report() == chapter_twelve_report()
    assert chapter_twelve_report().startswith("CHAPTER 12 — BUILDING AND MANAGING THE ENGAGEMENT PIPELINE")
    assert "Activities: 6\nEvidence-state changes: 0" in chapter_twelve_report()
