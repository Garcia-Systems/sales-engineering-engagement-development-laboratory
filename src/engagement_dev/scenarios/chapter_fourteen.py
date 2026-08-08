"""Chapter 14: descriptive process analytics and controlled improvement."""

from dataclasses import dataclass, replace

from engagement_dev.domain import (
    ClosureReason,
    CycleRetrospective,
    EngagementDevelopmentHistory,
    ImprovementExperiment,
    ImprovementPlan,
    OutreachStatus,
    ProcessMetrics,
)
from engagement_dev.scenarios.chapter_thirteen import analyze_chapter_thirteen
from engagement_dev.scenarios.chapter_twelve import analyze_chapter_twelve
from engagement_dev.services.analytics import ProcessAnalyzer


@dataclass(frozen=True)
class ChapterFourteenAnalysis:
    history: EngagementDevelopmentHistory
    metrics: ProcessMetrics
    retrospective: CycleRetrospective


def analyze_chapter_fourteen() -> ChapterFourteenAnalysis:
    twelve = analyze_chapter_twelve()
    thirteen = analyze_chapter_thirteen()
    # These are immutable projections of Chapter 12 records, not an analytics-owned
    # copy of lifecycle facts. Outcomes are attached to their existing attempts.
    outcome_statuses = (
        OutreachStatus.NO_RESPONSE,
        OutreachStatus.NO_RESPONSE,
        OutreachStatus.REPLIED,
    )
    projected = []
    outreach_items = [item for item in twelve.items if item.outreach]
    for item, status in zip(outreach_items, outcome_statuses):
        projected.append(replace(item, outreach=replace(item.outreach, status=status)))
    projected.extend(item for item in twelve.items if not item.outreach)
    # Keep UNKNOWN observable as a legitimate closure reason in this cycle.
    unknown = replace(thirteen.closures[-1], observed_reason=ClosureReason.UNKNOWN)
    closures = thirteen.closures + (unknown,)
    history = EngagementDevelopmentHistory(
        tuple(projected), closures, accounts_considered=20
    )
    analyzer = ProcessAnalyzer()
    metrics = analyzer.metrics(history)
    finding = analyzer.bottleneck(metrics)
    hypothesis = analyzer.improvement_hypothesis(finding)
    experiment = ImprovementExperiment(
        hypothesis,
        "outreach opening structure",
        "Cycle A uses a generic capability-led opening; Cycle B uses a signal-specific opening.",
        ("responses", "substantive conversations", "hypothesis updates"),
        (
            "Keep the offer constant",
            "Keep qualification policy constant",
            "Keep stopping rules constant",
        ),
        "In this deterministic exercise Cycle B produced more substantive responses.",
        (
            "The observation does not establish causation.",
            "The small sample does not establish a general rule.",
        ),
    )
    plan = ImprovementPlan(
        (experiment,),
        ("supported offer", "qualification policy", "stopping rules"),
        ("outreach opening structure",),
        experiment.observable_outcomes,
    )
    retrospective = CycleRetrospective(
        1,
        metrics,
        finding,
        (
            "Evidence-led research produced falsifiable hypotheses.",
            "Stakeholder conversations refined assumptions.",
        ),
        (
            "Whether wording caused response differences.",
            "Whether market selection explains outcomes.",
            "Whether results generalize beyond this cycle.",
        ),
        hypothesis,
        plan,
    )
    return ChapterFourteenAnalysis(history, metrics, retrospective)


def chapter_fourteen_report() -> str:
    analysis = analyze_chapter_fourteen()
    metrics, retrospective = analysis.metrics, analysis.retrospective
    transitions = {
        (x.from_state.value, x.to_state.value): x.observed_count
        for x in metrics.transitions
    }
    lines = [
        "CHAPTER 14 — ENGAGEMENT DEVELOPMENT ANALYTICS",
        "",
        "CYCLE SUMMARY",
        "",
        f"Candidate accounts                 {metrics.count('accounts_considered')}",
        f"Selected for research              {metrics.count('accounts_selected_for_research')}",
        f"Research briefs completed           {metrics.count('research_briefs_completed')}",
        f"Supported hypotheses                {metrics.count('hypotheses_supported')}",
        f"Stakeholder conversations           {metrics.count('stakeholder_conversations')}",
        f"Qualification assessments           {metrics.count('qualification_assessments')}",
        f"Engagement candidates               {metrics.count('engagement_candidates')}",
        "",
        "PIPELINE TRANSITIONS",
        "",
    ]
    for (left, right), count in transitions.items():
        lines.append(f"{left} → {right}  {count}")
    lines += ["", "TIME IN STATE", ""]
    lines += [
        f"{item.state.value}: {item.average_scenario_days:.1f} average scenario days ({item.observations} observations)"
        for item in metrics.time_in_state
    ]
    lines += ["", "CLOSURE REASONS", ""]
    lines += [f"{reason.value:40} {count}" for reason, count in metrics.closure_reasons]
    lines += [
        "",
        "ACTIVITY",
        "",
        f"Total recorded activities: {metrics.total_activities}",
        f"Activities producing new evidence: {metrics.evidence_producing_activities}",
        "Activities not classified as evidence-producing remain candidates for review, not proven waste.",
        "",
        "IMPORTANT",
        "",
        "Activity count is not a measure of opportunity quality.",
        "Response rate is an observed scenario association, not causal proof of message quality.",
        "",
        "MARKET COMPARISON",
        "",
    ]
    for market, values in metrics.market_counts:
        lines.append(
            f"{market}: "
            + ", ".join(f"{key.replace('_', ' ')}={value}" for key, value in values)
        )
    lines += [
        "This scenario comparison does not universally rank markets.",
        "",
        "OBSERVED BOTTLENECK",
        "",
        retrospective.primary_bottleneck.kind.value,
        "",
        "Evidence:",
        *[f"- {item}" for item in retrospective.primary_bottleneck.evidence],
        "",
        "Interpretation:",
        retrospective.primary_bottleneck.interpretation,
        "",
        "Causal explanation:",
        retrospective.primary_bottleneck.causal_explanation,
        "",
        "IMPROVEMENT HYPOTHESIS",
        "",
        retrospective.improvement_hypothesis.statement,
        "",
        "STATUS",
        "",
        retrospective.improvement_hypothesis.status.value,
        "",
        "NEXT-CYCLE EXPERIMENT",
        "",
        "Change:",
        *[f"- {item}" for item in retrospective.improvement_plan.changed_variables],
        "",
        "Keep constant:",
        *[f"- {item}" for item in retrospective.improvement_plan.keep_constant],
        "",
        "Observe:",
        *[f"- {item}" for item in retrospective.improvement_plan.observe],
        "",
        "INTERPRETATION LIMITS",
        *[
            f"- {item}"
            for item in retrospective.improvement_plan.experiments[
                0
            ].interpretation_limits
        ],
        "",
        "WARNINGS",
        *[warning.value for warning in metrics.warnings],
        "",
        "ENGAGEMENT CANDIDATES",
        "",
        str(metrics.count("engagement_candidates")),
        "",
        "CLOSED DEALS",
        "",
        "Not modeled.",
        "",
        "REVENUE FORECAST",
        "",
        "Not modeled.",
        "",
        "Metric ≠ Explanation | Correlation ≠ Causation | Activity ≠ Progress",
    ]
    return "\n".join(lines) + "\n"
