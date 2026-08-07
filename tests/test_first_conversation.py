from dataclasses import fields, replace

from engagement_dev.domain import (
    ConversationEvidence, ConversationQuestion, ConversationStage, EvidenceCategory,
    HypothesisOutcome, QuestionType, StakeholderStatement, StatementRelationship,
)
from engagement_dev.scenarios.chapter_nine import analyze_chapter_nine, chapter_nine_report
from engagement_dev.services import ConversationEvaluationOutcome, ConversationEvaluator


def test_statements_retain_conversation_source_and_category():
    analysis = analyze_chapter_nine()
    assert all(item.source_conversation_id == analysis.conversation.id for item in analysis.conversation.stakeholder_statements)
    assert all(item.evidence_category is EvidenceCategory.STAKEHOLDER_STATEMENT for item in analysis.conversation.stakeholder_statements)


def test_statements_remain_distinct_from_interpretations():
    captured = analyze_chapter_nine().conversation.evidence_captured[2]
    assert isinstance(captured, ConversationEvidence)
    assert "manually enter" in captured.statement.statement
    assert "business impact remain interpretations" in captured.interpretation
    assert captured.statement.statement != captured.interpretation


def test_neutral_and_assumption_loaded_questions_are_explainable():
    evaluator = ConversationEvaluator()
    assert evaluator.is_neutral("Where, if anywhere, does coordination become difficult?")
    assert not evaluator.is_neutral("How bad are your integration problems?")
    conversation = analyze_chapter_nine().conversation
    loaded = replace(conversation, questions=(ConversationQuestion(
        "How much money are these broken workflows costing?", QuestionType.IMPACT,
        ConversationStage.EXPLORE,
    ),))
    assert evaluator.evaluate(loaded).outcome is ConversationEvaluationOutcome.ASSUMPTION_LED


def test_follow_up_responds_to_disclosed_manual_work():
    statement = analyze_chapter_nine().conversation.stakeholder_statements[2]
    follow_up = ConversationEvaluator().select_follow_up(statement)
    assert follow_up.text == "Which event details have to be transferred manually?"
    assert follow_up.stage is ConversationStage.CLARIFY


def test_direct_evidence_weakens_inference_and_preserves_original_history():
    analysis = analyze_chapter_nine()
    assert analysis.revision.original.cautious_statement.startswith("Expansion may")
    assert analysis.revision.refined.cautious_statement.startswith("Event-booking information may")
    assert analysis.revision.original is not analysis.revision.refined
    assert analysis.conversation.id in analysis.revision.refined.evidence_ids
    assert analysis.conversation.stakeholder_statements[0].relationship is StatementRelationship.CONTRADICTS


def test_refutation_is_valid_discovery_and_no_current_opportunity():
    analysis = analyze_chapter_nine()
    assert analysis.refutation_revision.outcome is HypothesisOutcome.HYPOTHESIS_REFUTED
    assert analysis.refutation_conversation.hypothesis_outcome is HypothesisOutcome.HYPOTHESIS_REFUTED
    assert "NO_CURRENT_OPPORTUNITY" in analysis.refutation_conversation.next_step
    assert analysis.refutation_evaluation.outcome is ConversationEvaluationOutcome.DISCOVERY_COMPLETE


def test_new_information_does_not_automatically_become_opportunity():
    conversation = analyze_chapter_nine().conversation
    new = StakeholderStatement(
        "maya", "Our biggest issue is reconciling event deposits between systems.",
        "event deposits", EvidenceCategory.STAKEHOLDER_STATEMENT,
        StatementRelationship.INTRODUCES_NEW_INFORMATION, conversation.id,
    )
    assert new.relationship is StatementRelationship.INTRODUCES_NEW_INFORMATION
    assert conversation.qualified_opportunity_created is False


def test_manual_work_selects_neither_solution_nor_qualification():
    analysis = analyze_chapter_nine()
    assert analysis.selected_solution is None
    assert analysis.qualified_opportunity_created is False
    assert analysis.conversation.qualified_opportunity_created is False
    assert "Whether technology is the appropriate intervention" in analysis.conversation.unresolved_questions


def test_unknowns_and_evidence_ledger_remain_explicit():
    analysis = analyze_chapter_nine()
    assert "Business impact" in analysis.ledger.still_unknown
    assert "Budget" in analysis.ledger.still_unknown
    assert "Event booking remains separate" in analysis.ledger.known_from_stakeholder


def test_no_deal_value_or_purchase_probability_is_introduced():
    names = {item.name for item in fields(type(analyze_chapter_nine().conversation))}
    assert "deal_value" not in names
    assert "purchase_probability" not in names


def test_chapter_nine_output_is_deterministic_and_teaches_boundaries():
    first = chapter_nine_report()
    assert first == chapter_nine_report()
    assert "HYPOTHESIS_REFINED" in first
    assert "HYPOTHESIS_REFUTED" in first
    assert "QUALIFIED OPPORTUNITY\nNo." in first
    assert "SELECTED SOLUTION\nNone." in first
