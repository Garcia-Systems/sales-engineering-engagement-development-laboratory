"""Chapter 10: qualify evidence before crossing into a formal engagement."""

from dataclasses import dataclass, replace

from engagement_dev.domain import (
    Account, EngagementCandidate, EngagementHandoff, EvidenceCategory, ExternalHelpState,
    ImpactState, KnowledgeState, OwnershipState, PriorityState, ProblemState,
    ProviderFitState, QualificationAssessment, QualificationDimension,
    QualificationDimensionName as Name, QualificationOutcome, StakeholderStatement,
    StatementRelationship, TimingState,
)
from engagement_dev.scenarios.chapter_nine import analyze_chapter_nine
from engagement_dev.scenarios.chapter_seven import analyze_chapter_seven
from engagement_dev.services import QualificationEvaluator, create_engagement_candidate

UNKNOWNS = (
    "exact budget", "detailed integration architecture", "final technical approver",
    "procurement process", "solution options", "implementation scope",
)
OBJECTIVE = (
    "Determine whether a practical change to the event-information workflow can reduce "
    "repeated manual transfer while respecting existing platform constraints."
)


def _statement(identifier: str, stakeholder_id: str, text: str, topic: str) -> StakeholderStatement:
    return StakeholderStatement(
        stakeholder_id, text, topic, EvidenceCategory.STAKEHOLDER_STATEMENT,
        StatementRelationship.SUPPORTS, "conversation-blue-heron-2", identifier,
    )


@dataclass(frozen=True)
class ChapterTenAnalysis:
    assessment: QualificationAssessment
    candidate: EngagementCandidate | None
    handoff: EngagementHandoff | None
    alternatives: tuple[QualificationAssessment, ...]
    history: tuple[QualificationAssessment, ...]
    threshold_evaluation: tuple[str, ...]


def analyze_chapter_ten() -> ChapterTenAnalysis:
    nine = analyze_chapter_nine()
    original = nine.revision.original
    refined = nine.revision.refined
    stakeholder_map = analyze_chapter_seven().stakeholder_map
    daniel = next(item for item in stakeholder_map.stakeholders if item.contact.id == "daniel")
    maya = next(item for item in stakeholder_map.stakeholders if item.contact.id == "maya")
    account = Account("blue-resort", "Blue Heron Resort", "hospitality")
    statements = (
        _statement("qev-problem", "maya", "Event coordinators repeatedly transfer banquet and event details into the property operational system.", "problem"),
        _statement("qev-impact", "maya", "The transfer consumes staff time and occasionally creates mismatched event information that requires correction.", "impact"),
        _statement("qev-priority", "daniel", "Reducing repeated event setup work is part of our active operational improvement initiative.", "priority"),
        _statement("qev-owner", "daniel", "I own the operational improvement initiative.", "ownership"),
        _statement("qev-timing", "daniel", "We want to investigate options before the fourth property begins hosting events.", "timing"),
        _statement("qev-approach", "maya", "Today coordinators manually transfer the details and then review them.", "current approach"),
        _statement("qev-constraint", "daniel", "The centralized reservation platform must remain because every property uses it.", "constraints"),
        _statement("qev-decision", "daniel", "I can sponsor an investigation, but an additional technology review would be required.", "decision process"),
        _statement("qev-external", "daniel", "Outside technical assistance could be considered if an initial investigation shows a practical path.", "external help"),
        _statement("qev-next", "daniel", "A deeper structured investigation should determine whether a practical path exists.", "agreed investigation"),
    )
    by_id = {item.id: item for item in statements}
    dim = lambda name, state, ids=(), explanation="", unknowns=(): QualificationDimension(name, state, ids, explanation, unknowns)
    dimensions = (
        dim(Name.PROBLEM, ProblemState.CONFIRMED, ("qev-problem",), by_id["qev-problem"].statement),
        dim(Name.IMPACT, ImpactState.CONFIRMED, ("qev-impact",), by_id["qev-impact"].statement, ("Financial impact has not been quantified.",)),
        dim(Name.PRIORITY, PriorityState.ACTIVE, ("qev-priority",), by_id["qev-priority"].statement),
        dim(Name.OWNERSHIP, OwnershipState.IDENTIFIED, ("qev-owner",), "Daniel Brooks owns the initiative; budget authority remains unknown."),
        dim(Name.TIMING, TimingState.UPCOMING, ("qev-timing",), by_id["qev-timing"].statement),
        dim(Name.CURRENT_APPROACH, KnowledgeState.KNOWN, ("qev-approach",), "Manual transfer plus review."),
        dim(Name.CONSTRAINTS, KnowledgeState.PARTIAL, ("qev-constraint",), "The centralized reservation platform remains in place."),
        dim(Name.DECISION_PROCESS, KnowledgeState.PARTIAL, ("qev-decision",), "Sponsorship is known; final technology approval and procurement are unknown."),
        dim(Name.PROVIDER_FIT, ProviderFitState.SUPPORTED, ("offer-problem-system-integration",), "The supported offer includes investigating system-integration and manual-workflow problem classes."),
        dim(Name.EXTERNAL_HELP, ExternalHelpState.POSSIBLY_OPEN, ("qev-external",), by_id["qev-external"].statement),
        dim(Name.AGREED_INVESTIGATION, KnowledgeState.KNOWN, ("qev-next",), by_id["qev-next"].statement),
        dim(Name.BUDGET, KnowledgeState.UNKNOWN, (), "No stakeholder established a budget.", ("Exact budget is unknown.",)),
    )
    evaluator = QualificationEvaluator()
    assessment = evaluator.evaluate(
        assessment_id="qualification-blue-heron-1", opportunity_hypothesis=original,
        refined_hypothesis=refined, dimensions=dimensions, unresolved_gaps=UNKNOWNS,
    )
    basic = create_engagement_candidate(candidate_id="engagement-blue-heron-1", account=account, hypothesis=refined, qualification=assessment)
    candidate = replace(
        basic, stakeholder_evidence=statements, known_stakeholders=(maya, daniel),
        business_impact_evidence=("qev-impact",), current_approach="Manual transfer plus review.",
        known_constraints=("Centralized reservation platform remains in place.",),
        timing="Investigation desired before fourth-property event operations begin.",
        unresolved_questions=UNKNOWNS, engagement_objective=OBJECTIVE, handoff_status="READY",
    )
    handoff = EngagementHandoff(
        account, refined.cautious_statement, statements, "Repeated staff effort and occasional correction work.",
        "Active operational improvement initiative.", daniel,
        "Investigation desired before fourth-property event operations begin.", "Manual transfer plus review.",
        candidate.known_constraints, "Potentially acceptable.", UNKNOWNS, OBJECTIVE,
    )

    def variant(identifier: str, changes: dict[Name, object]) -> QualificationAssessment:
        changed = tuple(replace(item, state=changes[item.name]) if item.name in changes else item for item in dimensions)
        return evaluator.evaluate(assessment_id=identifier, opportunity_hypothesis=original, refined_hypothesis=refined, dimensions=changed, unresolved_gaps=UNKNOWNS)

    alternatives = (
        variant("qualification-low-priority", {Name.PRIORITY: PriorityState.NOT_A_PRIORITY}),
        variant("qualification-internal-only", {Name.EXTERNAL_HELP: ExternalHelpState.INTERNAL_ONLY}),
        variant("qualification-insufficient-impact", {Name.PROBLEM: ProblemState.PARTIAL, Name.IMPACT: ImpactState.UNKNOWN}),
        variant("qualification-refuted", {Name.PROBLEM: ProblemState.REFUTED}),
    )
    postponed = variant("qualification-blue-heron-postponed", {Name.TIMING: TimingState.DEFERRED})
    threshold = (
        "specific problem confirmed", "meaningful impact confirmed", "priority active",
        "owner identified", "timing upcoming", "provider fit supported",
        "external help possibly open", "deeper investigation agreed",
    )
    return ChapterTenAnalysis(assessment, candidate, handoff, alternatives, (assessment, postponed), threshold)


def chapter_ten_report() -> str:
    analysis = analyze_chapter_ten()
    assessment, candidate = analysis.assessment, analysis.candidate
    lines = [
        "CHAPTER 10 — QUALIFYING THE OPPORTUNITY", "", "ACCOUNT", "Blue Heron Resort", "",
        "REFINED HYPOTHESIS", "", assessment.refined_hypothesis.cautious_statement, "", "---", "", "QUALIFICATION",
    ]
    shown = (Name.PROBLEM, Name.IMPACT, Name.PRIORITY, Name.OWNERSHIP, Name.TIMING, Name.CURRENT_APPROACH, Name.CONSTRAINTS, Name.DECISION_PROCESS, Name.EXTERNAL_HELP, Name.BUDGET)
    for name in shown:
        item = assessment.dimension(name)
        lines += ["", name.value, item.state.value]
        if name is Name.OWNERSHIP:
            lines += ["", "Owner:", "Daniel Brooks"]
        if item.explanation:
            lines += ["", "Evidence:" if item.evidence_ids else "Unknown:", item.explanation]
    lines += [
        "", "---", "", "OVERALL ASSESSMENT", "", assessment.outcome.value, "", "WHY", "",
        assessment.explanation, "", "Budget remains unknown. Decision process remains partial.", "", "---", "",
        "ENGAGEMENT CANDIDATE", "", "CREATED" if candidate else "NOT CREATED", "", "DEAL CLOSED", "", "No.",
        "", "SOLUTION SELECTED", "", "No.", "", "BUDGET CONFIRMED", "", "No.", "", "---", "",
        "HANDOFF READY", "", "Yes.", "", "NEXT STEP", "",
        "Begin the structured Sales Engineering engagement using the evidence-backed handoff package.",
    ]
    return "\n".join(lines) + "\n"
