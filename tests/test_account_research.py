from dataclasses import replace
from datetime import date, timedelta

import pytest

from engagement_dev.cli import main
from engagement_dev.domain import (
    EvidenceFreshness, PublicSourceType, ResearchClaimType, SourceReliability,
)
from engagement_dev.scenarios import (
    chapter_four_report, chapter_one_report, chapter_three_report, chapter_two_report,
    chapter_zero_report, evaluate_chapter_four, load_chapter_four,
)
from engagement_dev.services import (
    AccountResearchEvaluator, ResearchReadinessStatus, classify_freshness,
    classify_source_reliability,
)


def test_fact_observation_inference_and_unknown_are_distinct_first_class_data():
    brief = load_chapter_four()
    assert {item.claim_type for item in brief.evidence} == {
        ResearchClaimType.FACT, ResearchClaimType.OBSERVATION,
    }
    assert brief.inferences and brief.unknowns
    assert all(item.evidence_ids for item in brief.inferences)
    assert all(item.account_id == brief.account.id for item in brief.unknowns)


def test_research_evidence_retains_provenance_and_reliability_categories():
    brief = load_chapter_four()
    assert all(item.source and item.source_type and item.source_reliability and item.observed_on for item in brief.evidence)
    assert brief.evidence[0].source_type is PublicSourceType.COMPANY_WEBSITE
    assert brief.evidence[0].source_reliability is SourceReliability.PRIMARY_PUBLIC_SOURCE
    assert brief.evidence[5].source_reliability is SourceReliability.SECONDARY_PUBLIC_SOURCE
    assert classify_source_reliability(PublicSourceType.COMPANY_WEBSITE) is SourceReliability.PRIMARY_PUBLIC_SOURCE
    assert classify_source_reliability(PublicSourceType.PUBLIC_DIRECTORY) is SourceReliability.SECONDARY_PUBLIC_SOURCE
    assert classify_source_reliability(PublicSourceType.PUBLIC_SOCIAL_POST) is SourceReliability.UNVERIFIED_PUBLIC_CLAIM


def test_freshness_thresholds_are_deterministic_and_stale_is_visible():
    research_date = date(2026, 8, 1)
    assert classify_freshness(research_date, research_date) is EvidenceFreshness.CURRENT
    assert classify_freshness(research_date - timedelta(days=90), research_date) is EvidenceFreshness.CURRENT
    assert classify_freshness(research_date - timedelta(days=91), research_date) is EvidenceFreshness.AGING
    assert classify_freshness(research_date - timedelta(days=365), research_date) is EvidenceFreshness.AGING
    assert classify_freshness(research_date - timedelta(days=366), research_date) is EvidenceFreshness.STALE
    with pytest.raises(ValueError):
        classify_freshness(research_date + timedelta(days=1), research_date)
    assert "Freshness: STALE" in chapter_four_report()


def test_contradictory_evidence_is_preserved_and_surfaced():
    brief = load_chapter_four()
    conflict = brief.conflicts[0]
    assert set(conflict.evidence_ids) == {"r6", "r7"}
    assert set(conflict.evidence_ids) <= {item.id for item in brief.evidence}
    assert "CONFLICTING EVIDENCE" in chapter_four_report()
    unresolved = replace(brief, conflicts=(replace(conflict, requires_review=True),))
    assert AccountResearchEvaluator().evaluate(unresolved).status is ResearchReadinessStatus.CONFLICT_REQUIRES_REVIEW


def test_corroboration_does_not_create_customer_pain_or_downstream_objects():
    brief = load_chapter_four()
    assert len(brief.corroborated_observations[0].evidence_ids) > 1
    assert "do not establish customer pain" in brief.corroborated_observations[0].explanation
    assert not hasattr(brief, "opportunity_hypothesis")
    assert not hasattr(brief, "engagement_candidate")
    assert "No customer problem has been established." in chapter_four_report()


def test_readiness_and_stopping_rule_are_deterministic_without_qualification():
    first = evaluate_chapter_four()
    assert first == evaluate_chapter_four()
    assert first.status is ResearchReadinessStatus.RESEARCH_READY
    assert first.stop_broad_research
    no_unknowns = replace(load_chapter_four(), unknowns=())
    result = AccountResearchEvaluator().evaluate(no_unknowns)
    assert result.status is ResearchReadinessStatus.MORE_RESEARCH_NEEDED
    assert not result.stop_broad_research


def test_chapters_zero_through_four_and_cli_remain_deterministic(capsys):
    reports = (chapter_zero_report, chapter_one_report, chapter_two_report, chapter_three_report, chapter_four_report)
    assert all(report() == report() for report in reports)
    for chapter in range(5):
        assert main([f"chapter-{chapter}"]) == 0
        capsys.readouterr()
    assert main(["chapter-4"]) == 0
    first = capsys.readouterr().out
    assert main(["chapter-4"]) == 0
    assert capsys.readouterr().out == first == chapter_four_report()
    assert "No opportunity hypothesis created." in first
