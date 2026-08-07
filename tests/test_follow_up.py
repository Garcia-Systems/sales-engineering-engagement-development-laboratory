from dataclasses import replace
from datetime import date, timedelta

from engagement_dev.cli import main
from engagement_dev.domain import (
    FollowUpReason, FollowUpResponseOutcome, FollowUpStatus, StopReason,
)
from engagement_dev.scenarios import analyze_chapter_eleven, chapter_eleven_report
from engagement_dev.services import (
    FollowUpEvaluationOutcome, FollowUpEvaluator, FollowUpPolicy,
    FollowUpResponseInterpreter,
)


def test_no_response_is_epistemically_neutral():
    outcome = FollowUpResponseInterpreter().interpret(None)
    assert outcome is FollowUpResponseOutcome.NO_RESPONSE_OBSERVED
    assert outcome not in {
        FollowUpResponseOutcome.EXTERNAL_HELP_NOT_ACCEPTED,
        FollowUpResponseOutcome.REQUESTED_FOLLOW_UP,
    }
    analysis = analyze_chapter_eleven()
    assert not analysis.conversation_created
    assert not analysis.qualification_changed
    assert not analysis.engagement_candidate_created


def test_follow_up_requires_reason_and_rejects_checking_in_or_pressure():
    analysis = analyze_chapter_eleven()
    evaluator = FollowUpEvaluator()
    action = analysis.first_follow_up
    assert evaluator.evaluate(
        replace(action, reason=None), today=action.intended_timing,
        prior_interaction_date=date(2026, 1, 5),
    ).outcome is FollowUpEvaluationOutcome.NO_VALID_REASON
    for message in ("Just bumping this again.", "Can you please respond?"):
        assert evaluator.evaluate(
            replace(action, proposed_message=message), today=action.intended_timing,
            prior_interaction_date=date(2026, 1, 5),
        ).outcome is FollowUpEvaluationOutcome.PRESSURE_LANGUAGE


def test_timing_and_requested_event_are_respected():
    analysis = analyze_chapter_eleven()
    evaluator = FollowUpEvaluator()
    action = analysis.first_follow_up
    assert evaluator.evaluate(
        action, today=action.intended_timing - timedelta(days=1),
        prior_interaction_date=date(2026, 1, 5),
    ).outcome is FollowUpEvaluationOutcome.TOO_SOON
    assert analysis.requested_before.outcome is FollowUpEvaluationOutcome.DEFER_UNTIL_REQUESTED_TIME
    assert analysis.requested_after.outcome is FollowUpEvaluationOutcome.SUPPORTED


def test_declines_and_no_contact_close_and_block_sequences():
    analysis = analyze_chapter_eleven()
    assert analysis.decline_outcome is FollowUpResponseOutcome.EXTERNAL_HELP_NOT_ACCEPTED
    assert analysis.declined_sequence.status is FollowUpStatus.CLOSED
    assert analysis.declined_sequence.stopping_rule.reason is StopReason.EXPLICIT_DECLINE
    assert analysis.no_contact_outcome is FollowUpResponseOutcome.REQUESTED_NO_CONTACT
    assert analysis.no_contact_sequence.stopping_rule.reason is StopReason.REQUESTED_NO_CONTACT
    blocked = FollowUpEvaluator().evaluate(
        analysis.no_contact_sequence, today=date(2027, 1, 1),
        prior_interaction_date=date(2026, 1, 5),
    )
    assert blocked.outcome is FollowUpEvaluationOutcome.CONTRADICTS_STAKEHOLDER_REQUEST
    fresh_action = replace(
        analysis.first_follow_up,
        id="attempt-to-evade-no-contact",
        stopping_rule=replace(analysis.first_follow_up.stopping_rule),
    )
    strict_evaluator = FollowUpEvaluator(
        FollowUpPolicy(requested_no_contact_ids=(fresh_action.stakeholder.contact.id,))
    )
    assert strict_evaluator.evaluate(
        fresh_action, today=date(2027, 1, 1), prior_interaction_date=date(2026, 1, 5),
    ).outcome is FollowUpEvaluationOutcome.CONTRADICTS_STAKEHOLDER_REQUEST


def test_attempt_limit_and_close_loop_are_deterministic():
    analysis = analyze_chapter_eleven()
    evaluator = FollowUpEvaluator()
    assert analysis.close_evaluation.outcome is FollowUpEvaluationOutcome.CLOSE_SEQUENCE
    assert analysis.closed_sequence.status is FollowUpStatus.CLOSED
    assert evaluator.evaluate(
        replace(analysis.first_follow_up, attempt_count=2), today=date(2026, 2, 1),
        prior_interaction_date=date(2026, 1, 5),
    ).outcome is FollowUpEvaluationOutcome.TOO_MANY_ATTEMPTS


def test_new_evidence_is_a_new_supported_context():
    analysis = analyze_chapter_eleven()
    assert analysis.new_evidence_follow_up.reason is FollowUpReason.NEW_RELEVANT_EVIDENCE
    assert analysis.new_evidence_follow_up.evidence_context == (
        "public-fourth-property-open", "public-events-hiring",
    )
    assert analysis.new_evidence_evaluation.outcome is FollowUpEvaluationOutcome.SUPPORTED


def test_referral_preserves_provenance_without_assuming_interest():
    referral = analyze_chapter_eleven().referral
    assert referral.source_statement.source_conversation_id == "conversation-blue-heron-referral"
    assert referral.source_statement.stakeholder_id == referral.source_stakeholder_id
    assert referral.referred_contact.name == "Sofia Ramirez"
    assert referral.interest_confirmed is False


def test_chapter_eleven_cli_is_deterministic_and_chapters_zero_to_ten_still_run(capsys):
    for chapter in range(11):
        assert main([f"chapter-{chapter}"]) == 0
        capsys.readouterr()
    assert chapter_eleven_report() == chapter_eleven_report()
    assert main(["chapter-11"]) == 0
    output = capsys.readouterr().out
    assert output == chapter_eleven_report()
    assert "No response does not establish rejection or interest." in output
    assert "OUTREACH STATUS\nCLOSED" in output
    assert "INTEREST CONFIRMED\nNo." in output
    assert "no external message was sent" in output
