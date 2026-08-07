"""Chapter 9: simulate a first conversation that reduces uncertainty."""

from dataclasses import dataclass

from engagement_dev.domain import (
    Conversation, ConversationEvidence, ConversationEvidenceLedger, ConversationQuestion,
    ConversationStage, ConversationStatus, EvidenceCategory, HypothesisOutcome,
    HypothesisRevision, HypothesisStatus, OpportunityHypothesis, QuestionType,
    StakeholderStatement, StatementRelationship,
)
from engagement_dev.scenarios.chapter_eight import analyze_chapter_eight
from engagement_dev.scenarios.chapter_seven import analyze_chapter_seven
from engagement_dev.services import ConversationEvaluation, ConversationEvaluator


REFINED_HYPOTHESIS = (
    "Event-booking information may require repeated manual transfer into property "
    "operational workflows."
)

UNRESOLVED = (
    "Volume", "Frequency", "Error rate", "Labor cost", "Business impact", "Priority",
    "Whether anyone wants it changed", "Whether technology is the appropriate intervention",
    "Budget", "Decision process",
)


@dataclass(frozen=True)
class ChapterNineAnalysis:
    conversation: Conversation
    revision: HypothesisRevision
    ledger: ConversationEvidenceLedger
    evaluation: ConversationEvaluation
    refutation_conversation: Conversation
    refutation_revision: HypothesisRevision
    refutation_evaluation: ConversationEvaluation
    qualified_opportunity_created: bool = False
    selected_solution: str | None = None


def _statement(text: str, topic: str, relationship: StatementRelationship, conversation_id: str) -> StakeholderStatement:
    return StakeholderStatement(
        "maya", text, topic, EvidenceCategory.STAKEHOLDER_STATEMENT,
        relationship, conversation_id,
    )


def analyze_chapter_nine() -> ChapterNineAnalysis:
    prior = analyze_chapter_seven()
    original = prior.hypothesis
    outreach = analyze_chapter_eight().selected
    conversation_id = "conversation-blue-heron-1"
    statements = (
        _statement("Reservations are centralized, and the new property uses the same reservation platform.", "reservation workflow", StatementRelationship.CONTRADICTS, conversation_id),
        _statement("Event bookings still use a separate workflow.", "event workflow", StatementRelationship.REFINES, conversation_id),
        _statement("Our coordinators manually enter some banquet details into the property system.", "event information transfer", StatementRelationship.SUPPORTS, conversation_id),
        _statement("The expansion itself is not causing major reservation issues; event coordination is the more relevant area.", "expansion effect", StatementRelationship.REFINES, conversation_id),
    )
    evaluator = ConversationEvaluator()
    first = ConversationQuestion(
        "How are reservations and event workflows coordinated today?",
        QuestionType.CURRENT_STATE, ConversationStage.EXPLORE,
    )
    follow_up = evaluator.select_follow_up(statements[1])
    questions = (
        first,
        ConversationQuestion("What changes as the fourth property comes online?", QuestionType.CHANGE, ConversationStage.EXPLORE),
        follow_up,
        evaluator.select_follow_up(statements[2]),
        ConversationQuestion("Where, if anywhere, does coordination become difficult?", QuestionType.IMPACT, ConversationStage.CLARIFY),
    )
    evidence = (
        ConversationEvidence(statements[0], "Direct evidence weakens the expansion-wide coordination inference."),
        ConversationEvidence(statements[1], "The possible issue is narrower than the original hypothesis."),
        ConversationEvidence(statements[2], "Manual transfer is confirmed; duplicated effort and business impact remain interpretations."),
        ConversationEvidence(statements[3], "Reservation expansion is not the relevant workflow; event coordination may merit investigation."),
    )
    conversation = Conversation(
        conversation_id, "maya", (), "blue-resort", "maya", outreach.message.id,
        original.id, questions=questions, stakeholder_statements=statements,
        evidence_captured=evidence, hypothesis_outcome=HypothesisOutcome.HYPOTHESIS_REFINED,
        unresolved_questions=UNRESOLVED,
        next_step="Investigate frequency, impact, priority, and desired future state without selecting a solution.",
        status=ConversationStatus.COMPLETED,
    )
    refined = OpportunityHypothesis(
        "hyp-blue-heron-event-workflow", original.account_id, REFINED_HYPOTHESIS,
        tuple((*original.evidence_ids, conversation.id)), original.supporting_signal_ids,
        original.signal_cluster_id, original.relevant_problem_class_ids,
        "Stakeholder evidence narrows the possible issue from expansion-wide coordination to event-information transfer.",
        original.assumptions, original.unknowns, original.falsification_conditions,
        original.validation_questions, original.evidence_chain,
        HypothesisStatus.SUPPORTED_FOR_VALIDATION,
    )
    revision = HypothesisRevision(original, refined, statements, HypothesisOutcome.HYPOTHESIS_REFINED)
    ledger = ConversationEvidenceLedger(
        ("Expansion announced", "Systems hiring observed", "Reservation platform change observed"),
        ("Operational coordination complexity may be increasing",),
        ("Actual workflow", "Actual friction", "Business impact"),
        ("Reservations centralized", "New property uses the same reservation platform", "Event booking remains separate", "Some event information is manually transferred"),
        UNRESOLVED,
    )

    refutation_id = "conversation-blue-heron-refutation"
    refuting_statement = _statement(
        "The systems are already unified, expansion does not change the workflow, and we are not experiencing coordination issues.",
        "coordination", StatementRelationship.CONTRADICTS, refutation_id,
    )
    refutation = Conversation(
        refutation_id, "maya", (), "blue-resort", "maya", outreach.message.id, original.id,
        questions=(first, evaluator.select_follow_up(refuting_statement)),
        stakeholder_statements=(refuting_statement,),
        evidence_captured=(ConversationEvidence(refuting_statement, "Direct internal evidence refutes the unsupported coordination inference."),),
        hypothesis_outcome=HypothesisOutcome.HYPOTHESIS_REFUTED,
        unresolved_questions=("Whether conditions change in the future",),
        next_step="NO_CURRENT_OPPORTUNITY; record the learning and do not advance the account.",
        status=ConversationStatus.COMPLETED,
    )
    refutation_revision = HypothesisRevision(
        original, None, (refuting_statement,), HypothesisOutcome.HYPOTHESIS_REFUTED,
    )
    return ChapterNineAnalysis(
        conversation, revision, ledger, evaluator.evaluate(conversation), refutation,
        refutation_revision, evaluator.evaluate(refutation),
    )


def chapter_nine_report() -> str:
    analysis = analyze_chapter_nine()
    conversation = analysis.conversation
    original = analysis.revision.original
    statements = conversation.stakeholder_statements
    lines = [
        "CHAPTER 9 — RUNNING THE FIRST CONVERSATION", "", "ACCOUNT", "Blue Heron Resort", "",
        "STAKEHOLDER", "Maya Chen", "Operations Systems Coordinator", "", "OBJECTIVE",
        conversation.objective.value, "", "ORIGINAL HYPOTHESIS", original.cautious_statement,
    ]
    exchanges = (
        ("QUESTION", conversation.questions[0].text, statements[0]),
        ("FOLLOW-UP QUESTION", conversation.questions[2].text, statements[1]),
        ("FOLLOW-UP QUESTION", conversation.questions[3].text, statements[2]),
    )
    for label, question, statement in exchanges:
        lines += ["", "---", "", label, question, "", "STAKEHOLDER", statement.statement, "", "EVIDENCE EFFECT", statement.relationship.value]
    lines += [
        "", "---", "", "HYPOTHESIS OUTCOME", conversation.hypothesis_outcome.value, "", "ORIGINAL",
        original.cautious_statement, "", "REFINED", analysis.revision.refined.cautious_statement, "",
        "WHAT WE NOW KNOW", *[f"- {item}" for item in analysis.ledger.known_from_stakeholder], "",
        "WHAT WE STILL DO NOT KNOW", *[f"- {item}" for item in analysis.ledger.still_unknown], "",
        "QUALIFIED OPPORTUNITY", "No.", "", "SELECTED SOLUTION", "None.", "", "WHY",
        "The conversation established a more specific possible problem, but material business impact and organizational priority remain unknown.",
        "", "CONVERSATION EVALUATION", analysis.evaluation.outcome.value, "",
        "SECONDARY REFUTATION SCENARIO", analysis.refutation_conversation.stakeholder_statements[0].statement,
        "", "HYPOTHESIS OUTCOME", "HYPOTHESIS_REFUTED", "", "NEXT STATE", "NO_CURRENT_OPPORTUNITY",
        "", "WHY THIS IS SUCCESSFUL", "Direct stakeholder evidence reduced uncertainty and prevented pursuit of an unsupported opportunity.",
    ]
    return "\n".join(lines) + "\n"
