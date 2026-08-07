from dataclasses import replace

import pytest

from engagement_dev.domain import (
    ExternalHelpState, ImpactState, KnowledgeState, OwnershipState, PriorityState,
    ProblemState, ProviderFitState, QualificationDimension, QualificationDimensionName as Name,
    QualificationOutcome, TimingState, UnqualifiedEngagementError,
)
from engagement_dev.scenarios.chapter_ten import OBJECTIVE, UNKNOWNS, analyze_chapter_ten, chapter_ten_report
from engagement_dev.services import QualificationEvaluator, create_engagement_candidate


def test_non_unknown_qualification_dimensions_require_evidence():
    with pytest.raises(ValueError, match="requires evidence"):
        QualificationDimension(Name.PROBLEM, ProblemState.CONFIRMED)
    unknown = QualificationDimension(Name.BUDGET, KnowledgeState.UNKNOWN)
    assert unknown.evidence_ids == ()


def test_all_dimensions_are_explicit_and_unknowns_stay_unknown():
    assessment = analyze_chapter_ten().assessment
    assert {item.name for item in assessment.dimensions} == set(Name)
    budget = assessment.dimension(Name.BUDGET)
    assert budget.state is KnowledgeState.UNKNOWN
    assert budget.evidence_ids == ()


def _evaluate_with(changes):
    analysis = analyze_chapter_ten()
    dimensions = tuple(
        replace(item, state=changes[item.name]) if item.name in changes else item
        for item in analysis.assessment.dimensions
    )
    return QualificationEvaluator().evaluate(
        assessment_id="changed", opportunity_hypothesis=analysis.assessment.opportunity_hypothesis,
        refined_hypothesis=analysis.assessment.refined_hypothesis, dimensions=dimensions,
    )


@pytest.mark.parametrize(("changes", "outcome"), (
    ({Name.IMPACT: ImpactState.UNKNOWN}, QualificationOutcome.MORE_DISCOVERY_NEEDED),
    ({Name.PRIORITY: PriorityState.NOT_A_PRIORITY}, QualificationOutcome.NOT_CURRENT_PRIORITY),
    ({Name.OWNERSHIP: OwnershipState.UNKNOWN}, QualificationOutcome.NO_CLEAR_OWNER),
    ({Name.TIMING: TimingState.DEFERRED}, QualificationOutcome.TIMING_NOT_ACTIVE),
    ({Name.PROVIDER_FIT: ProviderFitState.NOT_A_FIT}, QualificationOutcome.NOT_A_FIT),
    ({Name.EXTERNAL_HELP: ExternalHelpState.INTERNAL_ONLY}, QualificationOutcome.EXTERNAL_HELP_NOT_ACCEPTED),
    ({Name.PROBLEM: ProblemState.REFUTED}, QualificationOutcome.NO_CURRENT_OPPORTUNITY),
))
def test_each_material_threshold_dimension_matters(changes, outcome):
    assert _evaluate_with(changes).outcome is outcome


def test_confirmed_problem_alone_does_not_qualify():
    changes = {
        Name.IMPACT: ImpactState.UNKNOWN, Name.PRIORITY: PriorityState.UNKNOWN,
        Name.OWNERSHIP: OwnershipState.UNKNOWN, Name.TIMING: TimingState.UNDEFINED,
        Name.PROVIDER_FIT: ProviderFitState.UNKNOWN, Name.EXTERNAL_HELP: ExternalHelpState.UNKNOWN,
        Name.AGREED_INVESTIGATION: KnowledgeState.UNKNOWN,
    }
    assert _evaluate_with(changes).outcome is QualificationOutcome.NO_CLEAR_OWNER


def test_unknown_budget_does_not_block_a_qualified_engagement():
    analysis = analyze_chapter_ten()
    assert analysis.assessment.outcome is QualificationOutcome.QUALIFIED_FOR_ENGAGEMENT
    assert analysis.assessment.dimension(Name.BUDGET).state is KnowledgeState.UNKNOWN
    assert analysis.candidate is not None


def test_alternative_scenarios_are_selective():
    outcomes = [item.outcome for item in analyze_chapter_ten().alternatives]
    assert outcomes == [
        QualificationOutcome.NOT_CURRENT_PRIORITY,
        QualificationOutcome.EXTERNAL_HELP_NOT_ACCEPTED,
        QualificationOutcome.MORE_DISCOVERY_NEEDED,
        QualificationOutcome.NO_CURRENT_OPPORTUNITY,
    ]


def test_only_qualified_assessment_creates_candidate():
    analysis = analyze_chapter_ten()
    with pytest.raises(UnqualifiedEngagementError):
        create_engagement_candidate(
            candidate_id="blocked", account=analysis.handoff.account,
            hypothesis=analysis.assessment.refined_hypothesis,
            qualification=analysis.alternatives[0],
        )


def test_candidate_and_handoff_preserve_boundary_and_unknowns():
    analysis = analyze_chapter_ten()
    candidate, handoff = analysis.candidate, analysis.handoff
    assert candidate.handoff_status == "READY"
    assert candidate.unresolved_questions == UNKNOWNS == handoff.unknowns
    assert candidate.engagement_objective == OBJECTIVE == handoff.engagement_objective
    assert "solution" not in candidate.__dataclass_fields__
    assert "close_probability" not in candidate.__dataclass_fields__
    assert "contract_value" not in candidate.__dataclass_fields__
    assert "Determine whether" in handoff.engagement_objective
    assert "build an integration" not in handoff.engagement_objective.casefold()


def test_reassessment_preserves_history():
    history = analyze_chapter_ten().history
    assert [item.outcome for item in history] == [
        QualificationOutcome.QUALIFIED_FOR_ENGAGEMENT,
        QualificationOutcome.TIMING_NOT_ACTIVE,
    ]
    assert history[0].id != history[1].id


def test_chapter_ten_report_is_deterministic_and_explicit():
    assert chapter_ten_report() == chapter_ten_report()
    report = chapter_ten_report()
    for text in ("QUALIFIED_FOR_ENGAGEMENT", "BUDGET\nUNKNOWN", "DEAL CLOSED\n\nNo.", "SOLUTION SELECTED\n\nNo.", "HANDOFF READY\n\nYes."):
        assert text in report
