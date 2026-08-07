"""Focused Chapter 9 debugger laboratory."""

from engagement_dev.scenarios.chapter_nine import analyze_chapter_nine
from engagement_dev.services import ConversationEvaluator


analysis = analyze_chapter_nine()
current_hypothesis = analysis.revision.original
question = analysis.conversation.questions[1]
stakeholder_statement = analysis.conversation.stakeholder_statements[1]
statement_relationship = stakeholder_statement.relationship
evidence_ledger = analysis.ledger

# Set a breakpoint on the next line: this statement changes the interpretation.
follow_up_question = ConversationEvaluator().select_follow_up(stakeholder_statement)
hypothesis_outcome = analysis.conversation.hypothesis_outcome
unresolved_unknowns = analysis.conversation.unresolved_questions

print(follow_up_question.text)
