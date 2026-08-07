from dataclasses import replace

import pytest

from engagement_dev.cli import main
from engagement_dev.domain import HypothesisStatus, OutreachChannel, OutreachEvidence, OutreachStatus
from engagement_dev.scenarios import analyze_chapter_eight, chapter_eight_report
from engagement_dev.services import OutreachChannelAdapter, OutreachEvaluationOutcome, OutreachEvaluator


def _evaluate(message):
    analysis = analyze_chapter_eight()
    stakeholder = __import__("engagement_dev.scenarios", fromlist=["analyze_chapter_seven"]).analyze_chapter_seven().stakeholder_map.stakeholders[0]
    return OutreachEvaluator().evaluate(message, account_evidence_ids=("r4", "r5", "r5-news-1", "r5-news-2", "r5-news-3", "r7"), stakeholder=stakeholder, proof_artifact_ids=("inventory-lab", "banking-lab", "workflow-prototype"))


def test_factual_claims_require_account_evidence():
    message = analyze_chapter_eight().candidates[0].message
    unsupported = replace(message, factual_claims=(OutreachEvidence("Blue Heron is losing money.", ("invented",)),))
    assert _evaluate(unsupported).outcome is OutreachEvaluationOutcome.UNSUPPORTED_CLAIM


def test_hypothesis_cannot_silently_become_fact_and_solution_first_is_rejected():
    candidates = analyze_chapter_eight().candidates
    assert candidates[1].evaluation.outcome is OutreachEvaluationOutcome.REJECTED_ASSUMPTIONS
    assert candidates[4].evaluation.outcome is OutreachEvaluationOutcome.SOLUTION_PREMATURE


def test_stakeholder_relevance_and_generic_classification():
    candidates = analyze_chapter_eight().candidates
    assert candidates[0].message.stakeholder_id == "maya"
    assert candidates[2].evaluation.outcome is OutreachEvaluationOutcome.INSUFFICIENT_RELEVANCE


def test_credibility_requires_proof_and_fabricated_social_proof_is_rejected():
    message = analyze_chapter_eight().candidates[0].message
    assert _evaluate(replace(message, credibility_proof_ids=("imaginary-case-study",))).outcome is OutreachEvaluationOutcome.UNSUPPORTED_CLAIM
    assert _evaluate(replace(message, body=message.body + " Our customers saved millions.")).outcome is OutreachEvaluationOutcome.UNSUPPORTED_CLAIM


def test_aggressive_cta_and_overloaded_message_are_flagged():
    message = analyze_chapter_eight().candidates[0].message
    aggressive = replace(message, call_to_action="Can you schedule a demo?", body=message.body + " Can you schedule a demo?")
    assert _evaluate(aggressive).outcome is OutreachEvaluationOutcome.CTA_TOO_AGGRESSIVE
    assert analyze_chapter_eight().candidates[3].evaluation.outcome is OutreachEvaluationOutcome.TOO_BROAD


def test_supported_outreach_reaches_ready_but_is_never_sent():
    analysis = analyze_chapter_eight()
    assert analysis.selected.status is OutreachStatus.READY
    assert analysis.selected.actual_message_sent is False
    with pytest.raises(ValueError, match="cannot send"):
        replace(analysis.selected, actual_message_sent=True)


def test_channel_adaptation_is_deterministic_and_network_is_concise():
    analysis = analyze_chapter_eight()
    message = analysis.selected.message
    adapter = OutreachChannelAdapter()
    network = adapter.render(message, OutreachChannel.PROFESSIONAL_NETWORK)
    assert network == adapter.render(message, OutreachChannel.PROFESSIONAL_NETWORK)
    assert network == analysis.professional_network_message
    assert len(network.split()) < len(message.body.split())


def test_evaluation_is_deterministic_and_preserves_boundaries():
    first, second = analyze_chapter_eight(), analyze_chapter_eight()
    assert first.candidates == second.candidates
    assert first.external_communication_performed is False
    assert first.hypothesis_validated is False
    assert first.qualified_engagement_created is False
    chapter_seven = __import__("engagement_dev.scenarios", fromlist=["analyze_chapter_seven"]).analyze_chapter_seven()
    assert chapter_seven.hypothesis.status is HypothesisStatus.SUPPORTED_FOR_VALIDATION


def test_chapter_eight_cli_and_chapters_zero_through_seven_are_deterministic(capsys):
    for chapter in range(9):
        assert main([f"chapter-{chapter}"]) == 0
        capsys.readouterr()
    assert chapter_eight_report() == chapter_eight_report()
    assert main(["chapter-8"]) == 0
    output = capsys.readouterr().out
    assert output == chapter_eight_report()
    assert "STATUS\nREADY" in output
    assert "ACTUAL MESSAGE SENT\nNo." in output
