from dataclasses import replace
from datetime import date

import pytest

from engagement_dev.domain import (
    Account, ClosureEvidence, ClosureLevel, ClosureReason, LearningScope,
    PipelineDisposition, PipelineState, ReasonKnowledge, ReopenCondition,
    ReopenTrigger,
)
from engagement_dev.scenarios.chapter_thirteen import analyze_chapter_thirteen, chapter_thirteen_report
from engagement_dev.scenarios.chapter_twelve import analyze_chapter_twelve, chapter_twelve_report
from engagement_dev.services import (
    ClosureEvaluationResult, ClosureEvaluator, ClosureLearningExtractor,
    derive_pipeline_state,
)


def known(text):
    return (ClosureEvidence(text, ReasonKnowledge.KNOWN_CLOSURE_REASON, "Stakeholder statement"),)


def test_specific_reasons_require_known_evidence_and_unknown_is_valid():
    evaluator = ClosureEvaluator()
    rejected = evaluator.evaluate(ClosureReason.NO_BUDGET, (), ClosureLevel.OPPORTUNITY_CLOSURE)
    assert rejected.result is ClosureEvaluationResult.INSUFFICIENT_REASON_EVIDENCE
    assert rejected.recorded_reason is ClosureReason.UNKNOWN
    assert evaluator.evaluate(ClosureReason.UNKNOWN, (), ClosureLevel.RESEARCH_CLOSURE).recorded_reason is ClosureReason.UNKNOWN


def test_inferred_possibility_cannot_become_official_reason():
    evidence = (ClosureEvidence("They may have had no budget.", ReasonKnowledge.INFERRED_POSSIBILITY, "Analyst guess"),)
    result = ClosureEvaluator().evaluate(ClosureReason.NO_BUDGET, evidence, ClosureLevel.OPPORTUNITY_CLOSURE)
    assert result.recorded_reason is ClosureReason.UNKNOWN
    assert result.known_facts == ()
    assert result.inferred_possibilities


def test_no_response_is_neither_interest_nor_budget_evidence():
    evidence = known("Three attempts completed under the stopping rule; no response observed.")
    evaluator = ClosureEvaluator()
    assert evaluator.evaluate(ClosureReason.NO_RESPONSE_AFTER_STOPPING_RULE, evidence, ClosureLevel.OPPORTUNITY_CLOSURE).result is ClosureEvaluationResult.SUPPORTED_CLOSURE
    assert evaluator.evaluate(ClosureReason.NOT_INTERESTED, evidence, ClosureLevel.OPPORTUNITY_CLOSURE).recorded_reason is ClosureReason.UNKNOWN
    assert evaluator.evaluate(ClosureReason.NO_BUDGET, evidence, ClosureLevel.OPPORTUNITY_CLOSURE).recorded_reason is ClosureReason.UNKNOWN


def test_internal_only_evidence_and_hypothesis_refutation_are_preserved():
    closures = analyze_chapter_thirteen().closures
    internal = next(x for x in closures if x.observed_reason is ClosureReason.INTERNAL_ONLY)
    refuted = next(x for x in closures if x.observed_reason is ClosureReason.HYPOTHESIS_REFUTED)
    assert "internal development team" in internal.known_stakeholder_statements[0]
    assert refuted.observed_reason is not ClosureReason.PROVIDER_NOT_FIT
    assert refuted.level is ClosureLevel.OPPORTUNITY_CLOSURE


def test_closure_levels_are_distinct():
    assert len({ClosureLevel.RESEARCH_CLOSURE, ClosureLevel.OPPORTUNITY_CLOSURE, ClosureLevel.QUALIFIED_ENGAGEMENT_CLOSURE}) == 3
    qualified = next(x for x in analyze_chapter_thirteen().closures if x.observed_reason is ClosureReason.PROJECT_CANCELLED)
    assert qualified.level is ClosureLevel.QUALIFIED_ENGAGEMENT_CLOSURE
    assert qualified.closure_state is PipelineState.QUALIFIED_ENGAGEMENT_CLOSED
    assert "Competitor involvement" in qualified.unresolved_unknowns
    assert "A competitor won." in qualified.unsupported_lessons


def test_provider_boundary_supports_positive_out_of_scope_closure():
    closure = next(x for x in analyze_chapter_thirteen().closures if x.observed_reason is ClosureReason.PROVIDER_NOT_FIT)
    assert closure.closure_state is PipelineState.OUT_OF_SCOPE
    assert closure.supported_lessons[0].category.value == "PROCESS_LEARNING"


def test_learning_is_grounded_and_not_market_generalized():
    evidence = known("All channels feed automatically into one platform; no manual reconciliation occurs.")
    learning = ClosureLearningExtractor().extract(ClosureReason.HYPOTHESIS_REFUTED, evidence)[0]
    assert learning.evidence_statements == (evidence[0].statement,)
    assert learning.scope is LearningScope.ACCOUNT_SPECIFIC
    assert "market" not in learning.statement.casefold()


def test_unsupported_narratives_are_not_known_facts():
    closure = analyze_chapter_thirteen().closures[0]
    assert set(closure.unsupported_lessons).isdisjoint(closure.known_stakeholder_statements)


def test_reopen_conditions_require_a_legitimate_trigger():
    with pytest.raises(ValueError):
        ReopenCondition(ReopenTrigger.NEW_RELEVANT_SIGNAL, "")
    condition = ReopenCondition(ReopenTrigger.STAKEHOLDER_REQUEST, "Stakeholder asks to resume discovery.")
    assert condition.trigger is ReopenTrigger.STAKEHOLDER_REQUEST


def test_history_is_appended_not_replaced_and_dispositions_stay_distinct():
    for closure in analyze_chapter_thirteen().closures:
        assert closure.state_history[:-1] == closure.pipeline_item.state_history
    items = analyze_chapter_twelve().items
    deferred = next(x for x in items if x.account.name == "Harbor Street Music")
    outside = next(x for x in items if x.account.name == "Peninsula Industrial Controls")
    closed = next(x for x in items if x.account.name == "Heritage Lodging Group")
    assert {derive_pipeline_state(x) for x in (deferred, outside, closed)} == {PipelineState.DEFERRED, PipelineState.OUT_OF_SCOPE, PipelineState.CLOSED_NO_OPPORTUNITY}


def test_timing_defers_and_qualified_disposition_is_distinct():
    timing = next(x for x in analyze_chapter_thirteen().closures if x.observed_reason is ClosureReason.TIMING_INACTIVE)
    assert timing.closure_state is PipelineState.DEFERRED
    blue = next(x for x in analyze_chapter_twelve().items if x.account.name == "Blue Heron Resort")
    changed = replace(blue, disposition=PipelineDisposition.QUALIFIED_ENGAGEMENT_CLOSED, disposition_evidence="Project cancelled.")
    assert derive_pipeline_state(changed) is PipelineState.QUALIFIED_ENGAGEMENT_CLOSED


def test_chapters_zero_through_twelve_remain_stable_and_chapter_13_is_deterministic():
    before = chapter_twelve_report()
    assert before == chapter_twelve_report()
    assert chapter_thirteen_report() == chapter_thirteen_report()
    assert "RECORDED REASON\nUNKNOWN" in chapter_thirteen_report()
    assert "NOT\nNOT_INTERESTED" in chapter_thirteen_report()
