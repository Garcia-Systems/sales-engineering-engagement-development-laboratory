"""Debugger laboratory: compare a permitted follow-up with a blocked later attempt."""

from dataclasses import replace
from datetime import date

from engagement_dev.scenarios.chapter_eleven import DAY_0, analyze_chapter_eleven
from engagement_dev.services import FollowUpEvaluator

analysis = analyze_chapter_eleven()
evaluator = FollowUpEvaluator()

previous_outreach = analysis.initial_outreach
response_state = "NO_RESPONSE_OBSERVED"
follow_up_reason = analysis.first_follow_up.reason
elapsed_deterministic_time = 7
stakeholder_request = None
attempt_count = analysis.first_follow_up.attempt_count
stopping_rule = analysis.first_follow_up.stopping_rule
evaluator_result = evaluator.evaluate(
    analysis.first_follow_up, today=date(2026, 1, 12), prior_interaction_date=DAY_0,
)

later_attempt = replace(analysis.first_follow_up, attempt_count=2)
attempt_count = later_attempt.attempt_count
stopping_rule = later_attempt.stopping_rule
evaluator_result = evaluator.evaluate(
    later_attempt, today=date(2026, 1, 30), prior_interaction_date=DAY_0,
)

print(evaluator_result.outcome.value)
