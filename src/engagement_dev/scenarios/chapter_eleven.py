"""Chapter 11: continue only when evidence supplies a legitimate reason."""

from dataclasses import dataclass, replace
from datetime import date

from engagement_dev.domain import (
    Account, Contact, EvidenceCategory, FollowUpAction, FollowUpReason,
    FollowUpResponseOutcome, FollowUpStatus, OutreachAttempt, OutreachStatus,
    StakeholderReferral, StakeholderStatement, StatementRelationship, StopReason,
    StoppingRuleState,
)
from engagement_dev.scenarios.chapter_eight import analyze_chapter_eight
from engagement_dev.scenarios.chapter_seven import analyze_chapter_seven
from engagement_dev.services import (
    FollowUpEvaluation, FollowUpEvaluator, FollowUpResponseInterpreter,
)

DAY_0 = date(2026, 1, 5)
DAY_7 = date(2026, 1, 12)
DAY_18 = date(2026, 1, 23)
EVENT_DAY = date(2026, 4, 1)
FOLLOW_UP_MESSAGE = (
    "I wanted to follow up on my note about event workflow coordination as Blue Heron expands. "
    "Has this become an area you are working on? If not, no problem."
)
CLOSE_MESSAGE = (
    "I'll close the loop here. If workflow coordination becomes relevant as the new property "
    "ramps up, I'd be happy to compare notes."
)


@dataclass(frozen=True)
class ChapterElevenAnalysis:
    initial_outreach: OutreachAttempt
    first_follow_up: FollowUpAction
    first_evaluation: FollowUpEvaluation
    final_follow_up: FollowUpAction
    close_evaluation: FollowUpEvaluation
    closed_sequence: FollowUpAction
    requested_follow_up: FollowUpAction
    requested_before: FollowUpEvaluation
    requested_after: FollowUpEvaluation
    decline_outcome: FollowUpResponseOutcome
    declined_sequence: FollowUpAction
    no_contact_outcome: FollowUpResponseOutcome
    no_contact_sequence: FollowUpAction
    referral: StakeholderReferral
    new_evidence_follow_up: FollowUpAction
    new_evidence_evaluation: FollowUpEvaluation
    conversation_created: bool = False
    qualification_changed: bool = False
    engagement_candidate_created: bool = False
    external_communication_performed: bool = False


def analyze_chapter_eleven() -> ChapterElevenAnalysis:
    stakeholder_map = analyze_chapter_seven().stakeholder_map
    maya = next(item for item in stakeholder_map.stakeholders if item.contact.id == "maya")
    daniel = next(item for item in stakeholder_map.stakeholders if item.contact.id == "daniel")
    account = Account("blue-resort", "Blue Heron Resort", "hospitality")
    initial = replace(
        analyze_chapter_eight().selected,
        status=OutreachStatus.SENT_SIMULATED,
    )
    evaluator = FollowUpEvaluator()
    first = FollowUpAction(
        "follow-up-maya-1", account, maya, initial,
        FollowUpReason.NO_RESPONSE_TO_INITIAL_OUTREACH,
        ("outreach-a", "r5"), FOLLOW_UP_MESSAGE, DAY_7,
        FollowUpStatus.PLANNED, attempt_count=0,
    )
    first_result = evaluator.evaluate(first, today=DAY_7, prior_interaction_date=DAY_0)
    first_sent = replace(first, status=FollowUpStatus.NO_RESPONSE, attempt_count=1)
    final = replace(
        first_sent, id="follow-up-maya-close", proposed_message=CLOSE_MESSAGE,
        intended_timing=DAY_18,
    )
    close_result = evaluator.evaluate(final, today=DAY_18, prior_interaction_date=DAY_7)
    closed = evaluator.close(final)

    requested = FollowUpAction(
        "follow-up-daniel-requested", account, daniel, initial,
        FollowUpReason.REQUESTED_FOLLOW_UP,
        ("conversation-blue-heron-requested",),
        "You asked me to reconnect once the fourth property starts event operations. "
        "That event is now underway; would comparing notes be useful?",
        EVENT_DAY, requested_event="fourth property starts event operations",
    )
    requested_before = evaluator.evaluate(
        requested, today=date(2026, 3, 1), prior_interaction_date=DAY_0,
    )
    requested_after_action = replace(requested, requested_event_observed=True)
    requested_after = evaluator.evaluate(
        requested_after_action, today=EVENT_DAY, prior_interaction_date=DAY_0,
    )

    interpreter = FollowUpResponseInterpreter()
    decline = interpreter.interpret(
        "We are handling this internally and aren't looking for outside help."
    )
    declined = evaluator.stop(first, StopReason.EXPLICIT_DECLINE)
    no_contact = interpreter.interpret("Please remove me from future outreach.")
    no_contact_sequence = evaluator.stop(first, StopReason.REQUESTED_NO_CONTACT)

    referral_statement = StakeholderStatement(
        "daniel", "This isn't my area. You should talk to Sofia Ramirez in Events.",
        "referral", EvidenceCategory.STAKEHOLDER_STATEMENT,
        StatementRelationship.INTRODUCES_NEW_INFORMATION,
        "conversation-blue-heron-referral", "follow-up-referral-statement",
    )
    referral = StakeholderReferral(
        "daniel", Contact("sofia", account.id, "Sofia Ramirez", "Events"),
        referral_statement,
    )
    new_evidence = FollowUpAction(
        "follow-up-maya-new-context", account, maya, initial,
        FollowUpReason.NEW_RELEVANT_EVIDENCE,
        ("public-fourth-property-open", "public-events-hiring"),
        "I noticed the new property has now opened. When I reached out earlier I was curious "
        "about coordination across event operations as the organization expanded. Has that "
        "changed at all now that the new location is live?",
        EVENT_DAY,
    )
    new_evidence_result = evaluator.evaluate(
        new_evidence, today=EVENT_DAY, prior_interaction_date=DAY_0,
    )
    return ChapterElevenAnalysis(
        initial, first, first_result, final, close_result, closed, requested,
        requested_before, requested_after, decline, declined, no_contact,
        no_contact_sequence, referral, new_evidence, new_evidence_result,
    )


def chapter_eleven_report() -> str:
    result = analyze_chapter_eleven()
    return "\n".join((
        "CHAPTER 11 — MANAGING FOLLOW-UP WITHOUT CHASING", "",
        "SCENARIO A — NO RESPONSE", "", "INITIAL OUTREACH",
        result.initial_outreach.status.value, "", "RESPONSE", "None observed.", "",
        "IMPORTANT", "", "No response does not establish rejection or interest.", "",
        "FOLLOW-UP EVALUATION", "", result.first_evaluation.outcome.value, "", "Reason:",
        "One concise follow-up is permitted under the current educational policy.", "",
        "FOLLOW-UP MESSAGE", result.first_follow_up.proposed_message, "",
        "SECOND RESPONSE", "None observed.", "", "NEXT ACTION",
        result.close_evaluation.outcome.value, "", "FINAL MESSAGE",
        result.final_follow_up.proposed_message, "", "STATUS",
        result.closed_sequence.status.value, "", "CURRENT CONVERSATION", "NONE", "",
        "QUALIFICATION CHANGE", "NONE", "", "ENGAGEMENT CANDIDATE", "NONE", "",
        "SCENARIO B — REQUESTED FOLLOW-UP", "", "STAKEHOLDER STATEMENT",
        '“Reach back out once the fourth property begins event operations.”', "",
        "FOLLOW-UP BEFORE EVENT", result.requested_before.outcome.value, "",
        "FOLLOW-UP AFTER EVENT", result.requested_after.outcome.value, "",
        "SCENARIO C — EXPLICIT DECLINE", "", "STAKEHOLDER",
        '“We’re handling this internally.”', "", "RESULT", result.decline_outcome.value,
        "", "OUTREACH STATUS", result.declined_sequence.status.value, "",
        "SCENARIO D — REFERRAL", "", "STAKEHOLDER",
        '“This is probably better discussed with Sofia Ramirez in Events.”', "", "RESULT",
        FollowUpReason.STAKEHOLDER_REFERRAL.value, "", "NEW CONTACT",
        result.referral.referred_contact.name, "", "INTEREST CONFIRMED", "No.", "",
        "SCENARIO E — NO CONTACT", "", "RESULT", result.no_contact_outcome.value, "",
        "OUTREACH STATUS", result.no_contact_sequence.status.value, "",
        "SCENARIO F — NEW RELEVANT EVIDENCE", "", "RESULT",
        result.new_evidence_evaluation.outcome.value, "", "BOUNDARY",
        "All communication is simulated; no external message was sent.",
    )) + "\n"
