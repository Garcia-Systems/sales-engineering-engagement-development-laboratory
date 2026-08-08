"""Chapter 13: evidence-backed closure and deliberately bounded learning."""

from dataclasses import dataclass
from datetime import date

from engagement_dev.domain import (
    Account, ClosureEvidence, ClosureLevel, ClosureReason, ClosureRecord,
    PipelineItem, PipelineState, PipelineStateEvent, ReasonKnowledge,
    ReopenCondition, ReopenTrigger,
)
from engagement_dev.scenarios.chapter_twelve import analyze_chapter_twelve
from engagement_dev.services import ClosureEvaluator, append_closure_record

CLOSURE_DATE = date(2026, 8, 7)


@dataclass(frozen=True)
class ChapterThirteenAnalysis:
    closures: tuple[ClosureRecord, ...]
    unsupported_budget_evaluation: object


def _item(account: Account, state: PipelineState) -> PipelineItem:
    return PipelineItem(
        account,
        state_history=(PipelineStateEvent(date(2026, 8, 1), state, "Prior evidence state preserved."),),
        last_meaningful_evidence_on=date(2026, 8, 1),
        last_meaningful_evidence_event="Prior evidence state established.",
    )


def _close(item, reason, level, evidence, unknowns, unsupported, reopen=None):
    evaluation = ClosureEvaluator().evaluate(reason, evidence, level, unknowns)
    return append_closure_record(
        item, evaluation, evidence=evidence, closure_date=CLOSURE_DATE,
        unknowns=unknowns, unsupported_lessons=unsupported, reopen_condition=reopen,
    )


def analyze_chapter_thirteen() -> ChapterThirteenAnalysis:
    known = ReasonKnowledge.KNOWN_CLOSURE_REASON
    colonial = _item(Account("colonial-harbor-hotel", "Colonial Harbor Hotel", "hospitality"), PipelineState.HYPOTHESIS_SUPPORTED)
    refuted_evidence = (ClosureEvidence(
        "All reservation channels feed into the same property-management platform automatically; we do not manually reconcile them.",
        known, "Stakeholder conversation",
    ),)
    refuted = _close(
        colonial, ClosureReason.HYPOTHESIS_REFUTED, ClosureLevel.OPPORTUNITY_CLOSURE,
        refuted_evidence, ("Other operational problems", "Budget", "Future initiatives"),
        ("Hospitality companies do not need integration work.", "The original market selection was wrong.", "The stakeholder was not interested in the provider."),
        ReopenCondition(ReopenTrigger.NEW_PROBLEM_EVIDENCE, "New evidence of a materially different workflow or initiative."),
    )

    no_response = _close(
        _item(Account("peninsula-home-closure", "Peninsula Home Services", "home-services"), PipelineState.AWAITING_RESPONSE),
        ClosureReason.NO_RESPONSE_AFTER_STOPPING_RULE, ClosureLevel.OPPORTUNITY_CLOSURE,
        (ClosureEvidence("Three attempts completed under the stopping rule; no response observed.", known, "Chapter 11 follow-up history"),),
        ("Whether the message was read", "Stakeholder interest", "Timing", "Budget", "Hypothesis correctness", "Contact appropriateness"),
        ("They were not interested.", "They had no budget.", "The message was not persuasive enough."),
    )

    internal = _close(
        _item(Account("seabreeze-logistics", "Seabreeze Logistics", "logistics"), PipelineState.MORE_DISCOVERY_NEEDED),
        ClosureReason.INTERNAL_ONLY, ClosureLevel.OPPORTUNITY_CLOSURE,
        (ClosureEvidence("Our internal development team owns this and we are not using outside firms.", known, "Stakeholder conversation"),),
        ("Future external-assistance policy",), ("Our offer is not valuable.",),
    )

    blue = next(item for item in analyze_chapter_twelve().items if item.account.name == "Blue Heron Resort")
    cancelled = _close(
        blue, ClosureReason.PROJECT_CANCELLED, ClosureLevel.QUALIFIED_ENGAGEMENT_CLOSURE,
        (ClosureEvidence("The expansion project has been cancelled, so we are stopping the workflow initiative.", known, "Stakeholder conversation"),),
        ("Competitor involvement", "Pricing considerations"),
        ("A competitor won.", "Pricing was wrong.", "The sales process failed."),
    )

    provider_fit = _close(
        _item(Account("peninsula-control-services", "Peninsula Control Services", "industrial"), PipelineState.MORE_DISCOVERY_NEEDED),
        ClosureReason.PROVIDER_NOT_FIT, ClosureLevel.OPPORTUNITY_CLOSURE,
        (ClosureEvidence("The need is industrial control engineering outside demonstrated capability.", known, "Qualification conversation and Chapter 1 boundary"),),
        (), ("Qualification failed.",),
    )

    timing = _close(
        _item(Account("harbor-events", "Harbor Events Group", "hospitality"), PipelineState.MORE_DISCOVERY_NEEDED),
        ClosureReason.TIMING_INACTIVE, ClosureLevel.OPPORTUNITY_CLOSURE,
        (ClosureEvidence("This is relevant, but we are not considering changes until next fiscal year.", known, "Stakeholder conversation"),),
        ("Budget",), ("They are not interested.",),
        ReopenCondition(ReopenTrigger.TIMING_TRIGGER, "Next fiscal year begins."),
    )

    # Debug here: desire proposes NO_BUDGET, but no known evidence supports it.
    unsupported_budget_evaluation = ClosureEvaluator().evaluate(
        ClosureReason.NO_BUDGET,
        (ClosureEvidence("Budget may have influenced the decision.", ReasonKnowledge.INFERRED_POSSIBILITY, "Analyst possibility"),),
        ClosureLevel.OPPORTUNITY_CLOSURE,
        ("Actual budget situation",),
    )
    return ChapterThirteenAnalysis((refuted, no_response, internal, cancelled, provider_fit, timing), unsupported_budget_evaluation)


def chapter_thirteen_report() -> str:
    analysis = analyze_chapter_thirteen()
    a, b, c, d, _, _ = analysis.closures
    lines = [
        "CHAPTER 13 — LEARNING FROM REJECTION, CLOSURE, AND LOST OPPORTUNITIES", "",
        "SCENARIO A — HYPOTHESIS REFUTED", "", "ACCOUNT", a.account.name, "", "HYPOTHESIS",
        "Multiple reservation channels may require manual synchronization.", "", "STAKEHOLDER EVIDENCE",
        '“All reservation channels feed into the same platform automatically.”', "", "CLOSURE REASON", a.observed_reason.value,
        "", "SUPPORTED LEARNING", "Multiple reservation channels did not create the hypothesized synchronization problem in this account.",
        "", "UNSUPPORTED CONCLUSIONS", *[f"- {x}" for x in a.unsupported_lessons], "", "---", "",
        "SCENARIO B — NO RESPONSE", "", "ATTEMPTS", "Initial outreach", "Follow-up", "Close-the-loop", "", "RESPONSES", "0", "", "KNOWN", "No response observed.", "", "UNKNOWN", "Why.", "", "CLOSURE REASON", b.observed_reason.value, "", "NOT", "NOT_INTERESTED", "", "---", "",
        "SCENARIO C — INTERNAL ONLY", "", "PROBLEM", "Confirmed.", "", "EXTERNAL HELP", "Not accepted.", "", "CLOSURE", c.observed_reason.value, "", "LEARNING", "A real problem does not automatically create an external engagement.", "", "---", "",
        "SCENARIO D — QUALIFIED ENGAGEMENT CLOSED", "", "PREVIOUS STATE", d.previous_state.value, "", "NEW EVIDENCE", "Expansion project cancelled.", "", "CLOSURE", d.observed_reason.value, "", "COMPETITOR WIN", "Unknown.", "", "PRICING PROBLEM", "Unknown.", "", "---", "", "UNSUPPORTED NO_BUDGET CHECK", "", "RESULT", analysis.unsupported_budget_evaluation.result.value, "", "RECORDED REASON", analysis.unsupported_budget_evaluation.recorded_reason.value, "", "RETROSPECTIVE SUMMARY", "",
        f"Closed investigations: {sum(x.closure_state is not PipelineState.DEFERRED for x in analysis.closures)}",
        f"Hypotheses refuted: {sum(x.observed_reason is ClosureReason.HYPOTHESIS_REFUTED for x in analysis.closures)}",
        f"No-response closures: {sum(x.observed_reason is ClosureReason.NO_RESPONSE_AFTER_STOPPING_RULE for x in analysis.closures)}",
        f"Internal-only: {sum(x.observed_reason is ClosureReason.INTERNAL_ONLY for x in analysis.closures)}",
        f"Qualified engagement closures: {sum(x.level is ClosureLevel.QUALIFIED_ENGAGEMENT_CLOSURE for x in analysis.closures)}",
        f"Unknown closure reasons: {sum(x.observed_reason is ClosureReason.UNKNOWN for x in analysis.closures)}",
    ]
    return "\n".join(lines) + "\n"
