"""Chapter 12: project existing lifecycle evidence into a deterministic portfolio."""

from dataclasses import dataclass, replace
from datetime import date

from engagement_dev.domain import (
    Account, ActivityEvent, ActivityType, EvidenceCategory, HypothesisStatus,
    OpportunityHypothesis, OutreachAttempt, OutreachChannel, OutreachMessage,
    OutreachObjective, OutreachStatus, PipelineCapacity, PipelineDisposition,
    PipelineItem, PipelineState, PipelineStateEvent,
)
from engagement_dev.scenarios.chapter_ten import analyze_chapter_ten
from engagement_dev.services import (
    CapacityAllocation, ExplainedHealthFinding, PipelineCapacityPlanner,
    PipelineHealthFinding, derive_pipeline_state, next_justified_action,
    pipeline_health, stale_items,
)

TODAY = date(2026, 8, 7)


@dataclass(frozen=True)
class ChapterTwelveAnalysis:
    items: tuple[PipelineItem, ...]
    allocation: CapacityAllocation
    health: tuple[ExplainedHealthFinding, ...]
    stale: tuple[PipelineItem, ...]
    capacity: PipelineCapacity
    engagement_candidates: int
    closed_deals: int = 0
    projected_revenue: None = None


def _hypothesis(account_id: str) -> OpportunityHypothesis:
    return OpportunityHypothesis(
        f"hypothesis-{account_id}", account_id,
        "Available evidence supports validating whether repeated operational handoffs create a relevant workflow problem.",
        (f"evidence-{account_id}",), (f"signal-{account_id}",),
        status=HypothesisStatus.SUPPORTED_FOR_VALIDATION,
    )


def _sent_outreach(account_id: str) -> OutreachAttempt:
    message = OutreachMessage(
        f"outreach-{account_id}", account_id, f"stakeholder-{account_id}",
        f"hypothesis-{account_id}", OutreachObjective.VALIDATE_HYPOTHESIS,
        OutreachChannel.EMAIL, "Observed operational change.",
        "The stakeholder is close to the workflow evidence.", "Bounded workflow investigation.",
        "Is this worth validating?", "Would a brief evidence-gathering conversation be useful?",
        (), (), "A concise fictional evidence-based message.",
    )
    return OutreachAttempt(message, OutreachStatus.SENT_SIMULATED)


def analyze_chapter_twelve() -> ChapterTwelveAnalysis:
    ten = analyze_chapter_ten()
    assert ten.candidate is not None
    blue_history = tuple(
        PipelineStateEvent(when, state, event) for when, state, event in (
            (date(2026, 7, 1), PipelineState.RESEARCHING, "Account research began."),
            (date(2026, 7, 3), PipelineState.SIGNAL_FOUND, "Supported signals recorded."),
            (date(2026, 7, 4), PipelineState.HYPOTHESIS_SUPPORTED, "Hypothesis supported for validation."),
            (date(2026, 7, 5), PipelineState.STAKEHOLDER_MAPPED, "Relevant evidence sources mapped."),
            (date(2026, 7, 6), PipelineState.OUTREACH_READY, "Evidence-based outreach reviewed."),
            (date(2026, 7, 8), PipelineState.AWAITING_RESPONSE, "Simulated send recorded."),
            (date(2026, 7, 12), PipelineState.CONVERSATION_ACTIVE, "Stakeholder conversation began."),
            (date(2026, 7, 15), PipelineState.MORE_DISCOVERY_NEEDED, "Qualification gaps recorded."),
            (date(2026, 7, 20), PipelineState.QUALIFIED_FOR_ENGAGEMENT, "Chapter 10 threshold passed."),
        )
    )
    blue = PipelineItem(
        ten.candidate.account, hypothesis=ten.assessment.refined_hypothesis,
        qualification=ten.assessment, engagement_candidate=ten.candidate,
        last_meaningful_evidence_on=date(2026, 7, 20),
        last_meaningful_evidence_event="Qualification threshold passed.",
        unresolved_questions=ten.candidate.unresolved_questions, state_history=blue_history,
    )
    colonial_account = Account("colonial-hotel", "Colonial Harbor Hotel", "hospitality")
    colonial = PipelineItem(
        colonial_account, hypothesis=_hypothesis(colonial_account.id),
        last_meaningful_evidence_on=date(2026, 7, 29),
        last_meaningful_evidence_event="Supported hypothesis recorded.",
        unresolved_questions=("Who is closest to the workflow evidence?",),
    )
    tidewater = PipelineItem(
        Account("tidewater-inn", "Tidewater Inn", "hospitality"),
        last_meaningful_evidence_on=date(2026, 8, 5),
        last_meaningful_evidence_event="Research session opened.",
        unresolved_questions=("Is there enough account-specific evidence?",),
    )
    peninsula_account = Account("peninsula-home", "Peninsula Home Services", "home-services")
    activities = tuple(
        ActivityEvent(when, kind, description) for when, kind, description in (
            (date(2026, 7, 21), ActivityType.OUTREACH_SENT_SIMULATED, "Initial outreach"),
            (date(2026, 7, 23), ActivityType.NOTE_ADDED, "Follow-up preparation"),
            (date(2026, 7, 25), ActivityType.FOLLOW_UP_ATTEMPTED, "Follow-up simulated"),
            (date(2026, 7, 26), ActivityType.NOTE_ADDED, "Account note added"),
            (date(2026, 7, 28), ActivityType.EVIDENCE_REVIEWED, "Silence reviewed without interpretation"),
            (date(2026, 7, 30), ActivityType.NOTE_ADDED, "Waiting-policy note added"),
        )
    )
    peninsula = PipelineItem(
        peninsula_account, hypothesis=_hypothesis(peninsula_account.id),
        outreach=_sent_outreach(peninsula_account.id),
        last_meaningful_evidence_on=date(2026, 7, 21),
        last_meaningful_evidence_event="Simulated outreach sent; no response observed.",
        state_history=(PipelineStateEvent(date(2026, 7, 21), PipelineState.AWAITING_RESPONSE, "Simulated send recorded."),),
        activities=activities,
    )
    deferred = PipelineItem(
        Account("harbor-music", "Harbor Street Music", "retail"),
        disposition=PipelineDisposition.DEFERRED,
        disposition_evidence="Research capacity is allocated elsewhere; revisit on 2026-09-01.",
        last_meaningful_evidence_on=date(2026, 7, 1),
        last_meaningful_evidence_event="Capacity-based deferral documented.",
    )
    closed = PipelineItem(
        Account("heritage", "Heritage Lodging Group", "hospitality"),
        disposition=PipelineDisposition.CLOSED_NO_OPPORTUNITY,
        disposition_evidence="Reasonable research found insufficient evidence and no supported hypothesis.",
        last_meaningful_evidence_on=date(2026, 7, 18),
        last_meaningful_evidence_event="Investigation closure documented.",
    )
    outside = PipelineItem(
        Account("peninsula-controls", "Peninsula Industrial Controls", "industrial"),
        disposition=PipelineDisposition.OUT_OF_SCOPE,
        disposition_evidence="Relevant work is specialized industrial control engineering outside the supported offer.",
        last_meaningful_evidence_on=date(2026, 7, 18),
        last_meaningful_evidence_event="Provider boundary matched.",
    )
    # Account order is the transparent tie-breaker inside each capacity kind.
    items = (tidewater, colonial, blue, peninsula, deferred, closed, outside)
    capacity = PipelineCapacity()
    allocation = PipelineCapacityPlanner().allocate(items, capacity)
    return ChapterTwelveAnalysis(
        items, allocation, pipeline_health(items, today=TODAY),
        stale_items(items, today=TODAY), capacity,
        sum(derive_pipeline_state(item) is PipelineState.QUALIFIED_FOR_ENGAGEMENT for item in items),
    )


def chapter_twelve_report() -> str:
    analysis = analyze_chapter_twelve()
    by_state: dict[PipelineState, list[PipelineItem]] = {}
    for item in analysis.items:
        by_state.setdefault(derive_pipeline_state(item), []).append(item)
    display_order = (
        PipelineState.QUALIFIED_FOR_ENGAGEMENT, PipelineState.MORE_DISCOVERY_NEEDED,
        PipelineState.AWAITING_RESPONSE, PipelineState.HYPOTHESIS_SUPPORTED,
        PipelineState.RESEARCHING, PipelineState.DEFERRED,
        PipelineState.CLOSED_NO_OPPORTUNITY, PipelineState.OUT_OF_SCOPE,
    )
    lines = ["CHAPTER 12 — BUILDING AND MANAGING THE ENGAGEMENT PIPELINE", "", "PIPELINE"]
    for state in display_order:
        if state in by_state:
            lines += ["", state.value, *[f"- {item.account.name}" for item in by_state[state]]]
    peninsula = next(item for item in analysis.items if item.account.name == "Peninsula Home Services")
    lines += ["", "---", "", "ACTIVITY VS PROGRESS", "", peninsula.account.name, "", "Activities:"]
    lines += [f"- {event.description}" for event in peninsula.activities]
    lines += ["", f"Activities: {len(peninsula.activities)}", "Evidence-state changes: 0", "", "Evidence-state movement:", "None", "", "Current state:", derive_pipeline_state(peninsula).value, "", "IMPORTANT", "", "More activity did not create more evidence."]
    lines += ["", "---", "", "DASHBOARD", "", f"{'ACCOUNT':28} {'STATE':28} NEXT ACTION"]
    for item in analysis.items:
        lines.append(f"{item.account.name:28} {derive_pipeline_state(item).value:28} {next_justified_action(item).description}")
    lines += ["", "---", "", "CAPACITY", "", "Deep research slots:", str(analysis.capacity.deep_research_slots), "", "Discovery conversation slots:", str(analysis.capacity.discovery_conversation_slots), "", "Formal handoff slots:", str(analysis.capacity.formal_handoff_slots), "", "SELECTED WORK"]
    lines += [f"{index}. {action.description} for {name}" for index, (name, action) in enumerate(analysis.allocation.selected, 1)]
    lines += ["", "WAITING"]
    for name, reason in analysis.allocation.waiting:
        lines += ["", name, "", "Reason:", reason]
    primary = next(item for item in analysis.health if item.finding is PipelineHealthFinding.BALANCED_PIPELINE)
    lines += ["", "---", "", "PIPELINE HEALTH", "", "Finding:", primary.finding.value, "", "Explanation:", primary.explanation, "", "Warning:", f"{len(analysis.stale)} stale item requires review."]
    lines += ["", "---", "", "PORTFOLIO EVIDENCE SUMMARY", "", f"Accounts under investigation: {len(analysis.items)}", f"Supported hypotheses: {sum(item.hypothesis is not None for item in analysis.items)}", f"Active stakeholder conversations: {sum(derive_pipeline_state(item) is PipelineState.CONVERSATION_ACTIVE for item in analysis.items)}", f"Qualified engagement candidates: {analysis.engagement_candidates}", f"Deferred accounts: {sum(derive_pipeline_state(item) is PipelineState.DEFERRED for item in analysis.items)}", f"Closed without opportunity: {sum(derive_pipeline_state(item) is PipelineState.CLOSED_NO_OPPORTUNITY for item in analysis.items)}"]
    lines += ["", "ENGAGEMENT CANDIDATES", "", str(analysis.engagement_candidates), "", "CLOSED DEALS", "", str(analysis.closed_deals), "", "PROJECTED REVENUE", "", "Not calculated."]
    return "\n".join(lines) + "\n"
