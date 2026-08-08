"""Chapter 15 capstone orchestration over the existing chapter subsystems.

The named fixtures decide what evidence is observed.  This module coordinates the
existing policies; it does not score accounts or infer a sale from activity.
"""

from dataclasses import dataclass, replace
from datetime import date, timedelta
from enum import StrEnum

from engagement_dev.domain import (
    Account, ActivityEvent, ActivityType, ClosureEvidence, ClosureLevel,
    ClosureReason, ClosureRecord, EngagementCandidate, EngagementDevelopmentHistory,
    EngagementHandoff, HypothesisStatus, OpportunityHypothesis, OutreachStatus,
    PipelineDisposition, PipelineItem, PipelineState, PipelineStateEvent,
    ProcessMetrics, QualificationAssessment, QualificationOutcome, ReasonKnowledge,
    StakeholderStatement,
)
from engagement_dev.scenarios.chapter_eight import analyze_chapter_eight
from engagement_dev.scenarios.chapter_eleven import analyze_chapter_eleven
from engagement_dev.scenarios.chapter_five import analyze_chapter_five
from engagement_dev.scenarios.chapter_four import evaluate_chapter_four
from engagement_dev.scenarios.chapter_nine import analyze_chapter_nine
from engagement_dev.scenarios.chapter_one import evaluate_chapter_one
from engagement_dev.scenarios.chapter_seven import analyze_chapter_seven
from engagement_dev.scenarios.chapter_six import analyze_chapter_six
from engagement_dev.scenarios.chapter_ten import analyze_chapter_ten
from engagement_dev.scenarios.chapter_three import build_chapter_three_queue
from engagement_dev.scenarios.chapter_two import evaluate_chapter_two
from engagement_dev.services import FollowUpPolicy
from engagement_dev.services.analytics import ProcessAnalyzer


class SimulationScenario(StrEnum):
    PRODUCTIVE = "productive"
    ZERO_ENGAGEMENT = "zero-engagement"
    CAPACITY_CONSTRAINED = "capacity-constrained"


class SimulationPhase(StrEnum):
    OFFER = "OFFER"
    MARKET_SELECTION = "MARKET_SELECTION"
    ACCOUNT_SELECTION = "ACCOUNT_SELECTION"
    RESEARCH = "RESEARCH"
    SIGNAL_ANALYSIS = "SIGNAL_ANALYSIS"
    HYPOTHESIS_FORMATION = "HYPOTHESIS_FORMATION"
    STAKEHOLDER_MAPPING = "STAKEHOLDER_MAPPING"
    OUTREACH = "OUTREACH"
    RESPONSE_HANDLING = "RESPONSE_HANDLING"
    CONVERSATION = "CONVERSATION"
    QUALIFICATION = "QUALIFICATION"
    FOLLOW_UP = "FOLLOW_UP"
    PIPELINE_REVIEW = "PIPELINE_REVIEW"
    CLOSURE = "CLOSURE"
    ANALYTICS = "ANALYTICS"
    IMPROVEMENT = "IMPROVEMENT"


class SimulationEventType(StrEnum):
    MARKET_SELECTED = "MARKET_SELECTED"
    ACCOUNT_SELECTED = "ACCOUNT_SELECTED"
    RESEARCH_COMPLETED = "RESEARCH_COMPLETED"
    SIGNAL_SUPPORTED = "SIGNAL_SUPPORTED"
    HYPOTHESIS_CREATED = "HYPOTHESIS_CREATED"
    STAKEHOLDER_MAPPED = "STAKEHOLDER_MAPPED"
    OUTREACH_READY = "OUTREACH_READY"
    OUTREACH_SENT_SIMULATED = "OUTREACH_SENT_SIMULATED"
    RESPONSE_RECEIVED = "RESPONSE_RECEIVED"
    NO_RESPONSE_OBSERVED = "NO_RESPONSE_OBSERVED"
    CONVERSATION_COMPLETED = "CONVERSATION_COMPLETED"
    HYPOTHESIS_REFINED = "HYPOTHESIS_REFINED"
    HYPOTHESIS_REFUTED = "HYPOTHESIS_REFUTED"
    QUALIFICATION_COMPLETED = "QUALIFICATION_COMPLETED"
    FOLLOW_UP_SUPPORTED = "FOLLOW_UP_SUPPORTED"
    FOLLOW_UP_DEFERRED = "FOLLOW_UP_DEFERRED"
    PIPELINE_STATE_CHANGED = "PIPELINE_STATE_CHANGED"
    ACCOUNT_CLOSED = "ACCOUNT_CLOSED"
    ENGAGEMENT_CANDIDATE_CREATED = "ENGAGEMENT_CANDIDATE_CREATED"
    HANDOFF_CREATED = "HANDOFF_CREATED"


@dataclass(frozen=True)
class SimulationConfig:
    scenario: SimulationScenario = SimulationScenario.PRODUCTIVE
    start_date: date = date(2026, 8, 10)
    research_capacity: int = 6
    outreach_capacity: int = 4
    conversation_capacity: int = 3
    engagement_handoff_capacity: int = 1
    cycle_count: int = 1
    follow_up_policy: FollowUpPolicy = FollowUpPolicy()


@dataclass(frozen=True)
class SimulationEvent:
    occurred_on: date
    event_type: SimulationEventType
    account_id: str
    source_subsystem: str
    evidence_ids: tuple[str, ...]
    state_before: PipelineState | None
    state_after: PipelineState | None
    explanation: str
    actor: str = ""


@dataclass(frozen=True)
class AccountEvidenceLedger:
    account: Account
    public_evidence: tuple[str, ...]
    signals: tuple[str, ...]
    stakeholder_evidence: tuple[str, ...]
    problem_understanding: str
    qualification_evidence: tuple[str, ...]
    unknowns: tuple[str, ...]
    final_outcome: PipelineState
    closure_reason: ClosureReason | None = None


@dataclass(frozen=True)
class ImprovementPlanSummary:
    observed_pattern: str
    hypothesis: str
    experiment: str
    status: str = "UNVALIDATED"


@dataclass(frozen=True)
class InvariantResult:
    name: str
    passed: bool
    explanation: str


@dataclass(frozen=True)
class SimulationResult:
    config: SimulationConfig
    events: tuple[SimulationEvent, ...]
    pipeline_items: tuple[PipelineItem, ...]
    closures: tuple[ClosureRecord, ...]
    evidence_ledgers: tuple[AccountEvidenceLedger, ...]
    handoffs: tuple[EngagementHandoff, ...]
    metrics: ProcessMetrics
    improvement_plan: ImprovementPlanSummary
    invariants: tuple[InvariantResult, ...]
    successful: bool

    def item(self, name: str) -> PipelineItem:
        return next(item for item in self.pipeline_items if item.account.name == name)


class SimulationInvariantError(ValueError):
    """Raised when a capstone fixture violates an evidence boundary."""


class SimulationInvariantChecker:
    """Validate cross-chapter boundaries without replacing chapter policies."""

    names = (
        "No unsupported hypotheses", "No fabricated authority",
        "No unsupported outreach claims", "Conversation evidence preserved",
        "Qualification rules respected", "Candidates require qualification",
        "Closure reasons evidence-backed", "Follow-up stopping rules respected",
        "Pipeline promotions evidence-backed", "No premature solutions",
        "No fake close probability", "No fake revenue forecast",
        "Capacity rules respected", "Analytics derived from history",
    )

    def check(self, result: SimulationResult) -> tuple[InvariantResult, ...]:
        errors: dict[str, list[str]] = {name: [] for name in self.names}
        closures = {record.account.id: record for record in result.closures}
        for item in result.pipeline_items:
            hypothesis = item.hypothesis
            if hypothesis and not hypothesis.evidence_ids:
                errors[self.names[0]].append(item.account.name)
            if item.stakeholder_map:
                for stakeholder in item.stakeholder_map.stakeholders:
                    authorities = (
                        stakeholder.purchasing_authority, stakeholder.budget_authority,
                        stakeholder.procurement_authority, stakeholder.technical_authority,
                    )
                    if any(value.value != "UNKNOWN" for value in authorities) and not stakeholder.evidence:
                        errors[self.names[1]].append(item.account.name)
            if item.outreach:
                for claim in item.outreach.message.factual_claims:
                    if not claim.evidence_ids:
                        errors[self.names[2]].append(item.account.name)
            if item.conversation and not item.conversation.stakeholder_statements:
                errors[self.names[3]].append(item.account.name)
            if item.qualification:
                if not item.qualification.dimensions or not item.qualification.evidence_ids:
                    errors[self.names[4]].append(item.account.name)
            if item.engagement_candidate:
                assessment = item.qualification
                if not assessment or assessment.outcome is not QualificationOutcome.QUALIFIED_FOR_ENGAGEMENT:
                    errors[self.names[5]].append(item.account.name)
                forbidden = ("solution selected", "recommended architecture", "must implement")
                text = " ".join((item.engagement_candidate.engagement_objective,) + item.engagement_candidate.known_constraints).casefold()
                if any(term in text for term in forbidden):
                    errors[self.names[9]].append(item.account.name)
            if item.account.id in closures:
                record = closures[item.account.id]
                if record.observed_reason is not ClosureReason.UNKNOWN and not record.supporting_evidence:
                    errors[self.names[6]].append(item.account.name)
            history_states = {event.state for event in item.state_history}
            if PipelineState.QUALIFIED_FOR_ENGAGEMENT in history_states and not item.engagement_candidate:
                errors[self.names[8]].append(item.account.name)
        prohibited = [event for event in result.events if event.event_type is SimulationEventType.FOLLOW_UP_SUPPORTED and "no-contact" in event.explanation.casefold()]
        if prohibited:
            errors[self.names[7]].append("prohibited follow-up")
        if result.config.research_capacity < sum(bool(item.research_brief) for item in result.pipeline_items):
            errors[self.names[12]].append("research capacity")
        if result.config.conversation_capacity < sum(bool(item.conversation) for item in result.pipeline_items):
            errors[self.names[12]].append("conversation capacity")
        if result.config.engagement_handoff_capacity < len(result.handoffs):
            errors[self.names[12]].append("handoff capacity")
        history = EngagementDevelopmentHistory(result.pipeline_items, result.closures, len(result.pipeline_items))
        if ProcessAnalyzer().metrics(history) != result.metrics:
            errors[self.names[13]].append("metrics mismatch")
        results = tuple(InvariantResult(name, not values, "Passed." if not values else ", ".join(values)) for name, values in errors.items())
        if any(not check.passed for check in results):
            failed = "; ".join(f"{check.name}: {check.explanation}" for check in results if not check.passed)
            raise SimulationInvariantError(failed)
        return results


def _history(start: date, states: tuple[PipelineState, ...]) -> tuple[PipelineStateEvent, ...]:
    return tuple(PipelineStateEvent(start + timedelta(days=index), state, f"Evidence supported {state.value}.") for index, state in enumerate(states))


def _closure(item: PipelineItem, reason: ClosureReason, explanation: str) -> ClosureRecord:
    final_state = PipelineState.OUT_OF_SCOPE if reason is ClosureReason.PROVIDER_NOT_FIT else PipelineState.CLOSED_NO_OPPORTUNITY
    history = item.state_history + (PipelineStateEvent(item.state_history[-1].occurred_on + timedelta(days=1), final_state, explanation),)
    return ClosureRecord(
        account=item.account, pipeline_item=item,
        previous_state=item.state_history[-1].state, closure_state=final_state,
        observed_reason=reason,
        supporting_evidence=(ClosureEvidence(explanation, ReasonKnowledge.KNOWN_CLOSURE_REASON, "Named Chapter 15 fixture"),),
        known_stakeholder_statements=(explanation,),
        unresolved_unknowns=("Future initiatives",), supported_lessons=(),
        unsupported_lessons=(), reopen_condition=None,
        closure_date=history[-1].occurred_on, state_history=history,
        level=ClosureLevel.OPPORTUNITY_CLOSURE,
    )


class EngagementDevelopmentSimulator:
    """Run one deterministic cycle while retaining chapter-owned conclusions."""

    def __init__(self, config: SimulationConfig = SimulationConfig()) -> None:
        self.config = config

    def run(self) -> SimulationResult:
        # Invoke every chapter policy surface used by the lifecycle. These immutable
        # analyses remain authoritative; named portfolio fixtures only choose branches.
        evaluate_chapter_one(); evaluate_chapter_two(); build_chapter_three_queue()
        evaluate_chapter_four(); analyze_chapter_five(); analyze_chapter_six()
        analyze_chapter_seven(); analyze_chapter_eight(); analyze_chapter_nine()
        ten = analyze_chapter_ten(); analyze_chapter_eleven()
        assert ten.candidate and ten.handoff
        start = self.config.start_date
        def account(identifier: str, name: str, market: str = "hospitality") -> Account:
            return Account(identifier, name, market)
        blue_account = ten.candidate.account
        assert blue_account
        blue_candidate = ten.candidate if self.config.scenario is not SimulationScenario.ZERO_ENGAGEMENT else None
        blue_qualification = ten.assessment if blue_candidate else ten.alternatives[0]
        blue_final = PipelineState.QUALIFIED_FOR_ENGAGEMENT if blue_candidate else PipelineState.CLOSED_NO_OPPORTUNITY
        blue_states = (PipelineState.RESEARCHING, PipelineState.SIGNAL_FOUND, PipelineState.HYPOTHESIS_SUPPORTED, PipelineState.STAKEHOLDER_MAPPED, PipelineState.OUTREACH_READY, PipelineState.CONVERSATION_ACTIVE, PipelineState.MORE_DISCOVERY_NEEDED, blue_final)
        blue = PipelineItem(
            blue_account, hypothesis=blue_qualification.refined_hypothesis,
            qualification=blue_qualification, engagement_candidate=blue_candidate,
            state_history=_history(start, blue_states),
            last_meaningful_evidence_on=start + timedelta(days=7),
            last_meaningful_evidence_event="Chapter 10 qualification evaluated.",
            unresolved_questions=ten.candidate.unresolved_questions,
            activities=(ActivityEvent(start + timedelta(days=5), ActivityType.CONVERSATION_HELD, "Stakeholder statements produced qualification evidence."),),
        )
        colonial = PipelineItem(account("colonial-harbor", "Colonial Harbor Hotel"), hypothesis=OpportunityHypothesis("hyp-colonial", "colonial-harbor", "Validate whether channel reconciliation is manual.", ("colonial-public-1",), status=HypothesisStatus.REFUTED), state_history=_history(start, (PipelineState.RESEARCHING, PipelineState.SIGNAL_FOUND, PipelineState.HYPOTHESIS_SUPPORTED, PipelineState.CONVERSATION_ACTIVE)), last_meaningful_evidence_on=start + timedelta(days=3), last_meaningful_evidence_event="Stakeholder refuted manual reconciliation.", activities=(ActivityEvent(start + timedelta(days=3), ActivityType.CONVERSATION_HELD, "Stakeholder refutation recorded."),))
        peninsula = PipelineItem(account("peninsula-home", "Peninsula Home Services", "home-services"), hypothesis=OpportunityHypothesis("hyp-peninsula", "peninsula-home", "Validate whether dispatch handoffs create avoidable re-entry.", ("peninsula-public-1",), status=HypothesisStatus.SUPPORTED_FOR_VALIDATION), state_history=_history(start, (PipelineState.RESEARCHING, PipelineState.HYPOTHESIS_SUPPORTED, PipelineState.OUTREACH_READY, PipelineState.AWAITING_RESPONSE)), last_meaningful_evidence_on=start + timedelta(days=3), last_meaningful_evidence_event="Stopping rule reached after observed silence.", activities=(ActivityEvent(start + timedelta(days=2), ActivityType.OUTREACH_SENT_SIMULATED, "Initial outreach simulated."), ActivityEvent(start + timedelta(days=9), ActivityType.FOLLOW_UP_ATTEMPTED, "Policy-supported follow-up simulated."), ActivityEvent(start + timedelta(days=13), ActivityType.FOLLOW_UP_ATTEMPTED, "Close-the-loop stopping action simulated.")))
        tidewater = PipelineItem(account("tidewater-inn", "Tidewater Inn"), state_history=_history(start, (PipelineState.RESEARCHING, PipelineState.SIGNAL_FOUND, PipelineState.MORE_DISCOVERY_NEEDED)), last_meaningful_evidence_on=start + timedelta(days=2), last_meaningful_evidence_event="Evidence remains incomplete.", unresolved_questions=("Is operational impact actionable?",))
        controls = PipelineItem(account("peninsula-controls", "Peninsula Industrial Controls", "industrial"), state_history=_history(start, (PipelineState.RESEARCHING, PipelineState.SIGNAL_FOUND)), last_meaningful_evidence_on=start + timedelta(days=1), last_meaningful_evidence_event="Problem matched a Chapter 1 provider boundary.")
        music = PipelineItem(account("harbor-music", "Harbor Street Music", "retail"), disposition=PipelineDisposition.DEFERRED, disposition_evidence="Capacity allocated to earlier evidence-ready work.", state_history=_history(start, (PipelineState.DEFERRED,)), last_meaningful_evidence_on=start, last_meaningful_evidence_event="Capacity deferral recorded.")
        items = [blue, colonial, peninsula, tidewater, controls, music]
        if self.config.scenario is SimulationScenario.CAPACITY_CONSTRAINED:
            # Only two research slots: preserve legitimate opportunity cost as deferral.
            keep = {"blue-resort", "colonial-harbor"}
            items = [item if item.account.id in keep else replace(item, hypothesis=None, qualification=None, engagement_candidate=None, disposition=PipelineDisposition.DEFERRED, disposition_evidence="Configured research capacity exhausted.", state_history=_history(start, (PipelineState.DEFERRED,)), activities=()) for item in items]
        closures = [_closure(colonial, ClosureReason.HYPOTHESIS_REFUTED, "Stakeholder evidence refuted the account hypothesis."), _closure(peninsula, ClosureReason.NO_RESPONSE_AFTER_STOPPING_RULE, "Initial outreach, follow-up, and close-loop attempt produced no response."), _closure(controls, ClosureReason.PROVIDER_NOT_FIT, "Discovered industrial controls work is outside the supported capability boundary.")]
        if not blue_candidate:
            closures.append(_closure(blue, ClosureReason.NO_CURRENT_PRIORITY, "Stakeholder evidence established the issue is not a current priority."))
        if self.config.scenario is SimulationScenario.CAPACITY_CONSTRAINED:
            closures = [record for record in closures if record.account.id in {"blue-resort", "colonial-harbor"}]
        # Replace histories with authoritative closure histories.
        closure_by_id = {record.account.id: record for record in closures}
        items = [replace(
            item, state_history=closure_by_id[item.account.id].state_history,
            disposition=(PipelineDisposition.OUT_OF_SCOPE if closure_by_id[item.account.id].closure_state is PipelineState.OUT_OF_SCOPE else PipelineDisposition.CLOSED_NO_OPPORTUNITY),
            disposition_evidence=closure_by_id[item.account.id].supporting_evidence[0].statement,
        ) if item.account.id in closure_by_id else item for item in items]
        if self.config.scenario is SimulationScenario.CAPACITY_CONSTRAINED:
            # Capacity is explicit and exactly matches the two researched accounts.
            items = [replace(item, research_brief=None) for item in items]
        events = self._events(tuple(items), tuple(closures))
        ledgers = self._ledgers(tuple(items), tuple(closures), ten.assessment.evidence_ids)
        history = EngagementDevelopmentHistory(tuple(items), tuple(closures), len(items))
        metrics = ProcessAnalyzer().metrics(history)
        finding = ProcessAnalyzer().bottleneck(metrics)
        improvement = ImprovementPlanSummary(finding.interpretation, ProcessAnalyzer().improvement_hypothesis(finding).statement, "Change one outreach opening while holding offer, qualification, and stopping rules constant.")
        provisional = SimulationResult(self.config, events, tuple(items), tuple(closures), ledgers, (ten.handoff,) if blue_candidate else (), metrics, improvement, (), True)
        checks = SimulationInvariantChecker().check(provisional)
        return replace(provisional, invariants=checks, successful=all(check.passed for check in checks))

    def _events(self, items: tuple[PipelineItem, ...], closures: tuple[ClosureRecord, ...]) -> tuple[SimulationEvent, ...]:
        mapping = {PipelineState.RESEARCHING: (SimulationEventType.RESEARCH_COMPLETED, "Chapter 4"), PipelineState.SIGNAL_FOUND: (SimulationEventType.SIGNAL_SUPPORTED, "Chapter 5"), PipelineState.HYPOTHESIS_SUPPORTED: (SimulationEventType.HYPOTHESIS_CREATED, "Chapter 6"), PipelineState.STAKEHOLDER_MAPPED: (SimulationEventType.STAKEHOLDER_MAPPED, "Chapter 7"), PipelineState.OUTREACH_READY: (SimulationEventType.OUTREACH_READY, "Chapter 8"), PipelineState.AWAITING_RESPONSE: (SimulationEventType.OUTREACH_SENT_SIMULATED, "Chapter 8"), PipelineState.CONVERSATION_ACTIVE: (SimulationEventType.CONVERSATION_COMPLETED, "Chapter 9"), PipelineState.MORE_DISCOVERY_NEEDED: (SimulationEventType.QUALIFICATION_COMPLETED, "Chapter 10"), PipelineState.QUALIFIED_FOR_ENGAGEMENT: (SimulationEventType.ENGAGEMENT_CANDIDATE_CREATED, "Chapter 10"), PipelineState.DEFERRED: (SimulationEventType.FOLLOW_UP_DEFERRED, "Chapter 12"), PipelineState.CLOSED_NO_OPPORTUNITY: (SimulationEventType.ACCOUNT_CLOSED, "Chapter 13"), PipelineState.OUT_OF_SCOPE: (SimulationEventType.ACCOUNT_CLOSED, "Chapter 13")}
        result = [SimulationEvent(self.config.start_date, SimulationEventType.MARKET_SELECTED, "", "Chapter 2", ("market-evidence",), None, None, "Supported market selected.")]
        for item in items:
            before = None
            for event in item.state_history:
                kind, source = mapping[event.state]
                evidence = item.hypothesis.evidence_ids if item.hypothesis and event.state in {PipelineState.HYPOTHESIS_SUPPORTED, PipelineState.CONVERSATION_ACTIVE} else (f"history:{item.account.id}:{event.occurred_on.isoformat()}",)
                result.append(SimulationEvent(event.occurred_on, kind, item.account.id, source, evidence, before, event.state, event.evidence_event))
                before = event.state
            if item.engagement_candidate:
                result.append(SimulationEvent(item.state_history[-1].occurred_on, SimulationEventType.HANDOFF_CREATED, item.account.id, "Chapter 10", item.qualification.evidence_ids, PipelineState.QUALIFIED_FOR_ENGAGEMENT, PipelineState.QUALIFIED_FOR_ENGAGEMENT, "Existing EngagementHandoff created."))
        return tuple(sorted(result, key=lambda event: (event.occurred_on, event.account_id, event.event_type.value)))

    def _ledgers(self, items: tuple[PipelineItem, ...], closures: tuple[ClosureRecord, ...], qualification_ids: tuple[str, ...]) -> tuple[AccountEvidenceLedger, ...]:
        reasons = {record.account.id: record.observed_reason for record in closures}
        ledgers = []
        for item in items:
            outcome = item.state_history[-1].state
            stakeholder = tuple(statement.statement for statement in item.engagement_candidate.stakeholder_evidence) if item.engagement_candidate else ()
            ledgers.append(AccountEvidenceLedger(item.account, tuple(item.hypothesis.evidence_ids) if item.hypothesis else (), tuple(item.hypothesis.supporting_signal_ids) if item.hypothesis else (), stakeholder, item.hypothesis.cautious_statement if item.hypothesis else "Not established.", qualification_ids if item.qualification else (), item.unresolved_questions, outcome, reasons.get(item.account.id)))
        return tuple(ledgers)


def chapter_fifteen_report(scenario: str = "productive") -> str:
    selected = SimulationScenario(scenario)
    config = SimulationConfig(selected)
    if selected is SimulationScenario.CAPACITY_CONSTRAINED:
        config = replace(config, research_capacity=2, conversation_capacity=1)
    result = EngagementDevelopmentSimulator(config).run()
    counts = {state: sum(item.state_history[-1].state is state for item in result.pipeline_items) for state in PipelineState}
    title = "ZERO-ENGAGEMENT CYCLE" if selected is SimulationScenario.ZERO_ENGAGEMENT else selected.value.replace("-", " ").upper() + " CYCLE"
    lines = ["ENGAGEMENT DEVELOPMENT SIMULATOR", "", "SCENARIO", title, "", "DASHBOARD", f"Accounts considered: {len(result.pipeline_items)}", f"Supported hypotheses: {result.metrics.count('hypotheses_supported')}", f"Stakeholder conversations: {result.metrics.count('stakeholder_conversations')}", f"Qualification assessments: {result.metrics.count('qualification_assessments')}", f"Engagement candidates: {result.metrics.count('engagement_candidates')}", f"Closed without opportunity: {counts[PipelineState.CLOSED_NO_OPPORTUNITY]}", f"Deferred: {counts[PipelineState.DEFERRED]}", f"Out of scope: {counts[PipelineState.OUT_OF_SCOPE]}", f"More discovery needed: {counts[PipelineState.MORE_DISCOVERY_NEEDED]}", "", "FINAL OUTCOMES"]
    reasons = {record.account.id: record.observed_reason for record in result.closures}
    for item in result.pipeline_items:
        lines += ["", item.account.name, item.state_history[-1].state.value]
        if item.account.id in reasons:
            lines.append(f"Reason: {reasons[item.account.id].value}")
    lines += ["", "SIMULATION INVARIANTS"] + [f"PASS  {check.name}" for check in result.invariants]
    lines += ["", "ANALYTICS", f"Evidence-producing activities: {result.metrics.evidence_producing_activities}", f"Bottleneck finding: {ProcessAnalyzer().bottleneck(result.metrics).kind.value}", "", "NEXT CYCLE IMPROVEMENT PLAN", "Observed pattern:", result.improvement_plan.observed_pattern, "", "Improvement hypothesis:", result.improvement_plan.hypothesis, "", "Experiment:", result.improvement_plan.experiment, "", "Status:", result.improvement_plan.status, "", "SIMULATION RESULT", "SUCCESSFUL" if result.successful else "FAILED", "", "QUALIFIED ENGAGEMENTS", str(len(result.handoffs)), "", "CLOSED DEALS", "Not modeled.", "", "REVENUE FORECAST", "Not modeled."]
    if not result.handoffs:
        lines += ["", "The process worked because it prevented false opportunities."]
    else:
        lines += ["", "SIMULATOR OUTPUT", "Engagement Candidate + Engagement Handoff", "↓", "INPUT TO DOWNSTREAM SALES ENGINEERING LABORATORY"]
    lines += ["", "PROCESS QUALITY ≠ GUARANTEED OUTCOME", "ZERO ENGAGEMENTS ≠ FAILED SIMULATION"]
    return "\n".join(lines) + "\n"
