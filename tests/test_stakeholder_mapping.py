from dataclasses import fields, replace

import pytest

from engagement_dev.cli import main
from engagement_dev.domain import (
    AuthorityStatus, Contact, EvidenceProximity, HypothesisStatus, KnowledgeDomain,
    OrganizationalRole, PublicSourceType, RelationshipType, Stakeholder,
    StakeholderClaimType, StakeholderEvidence,
)
from engagement_dev.scenarios import analyze_chapter_seven, chapter_seven_report
from engagement_dev.services import ContactPriority, CoverageStatus, DomainCoverage


def test_contacts_do_not_automatically_become_buyers_or_stakeholders():
    contact = Contact("person", "blue-resort", "A Person", "Chief Buyer")
    assert not hasattr(contact, "buyer")
    assert not isinstance(contact, Stakeholder)
    assert "buyer" not in {field.name for field in fields(contact)}


def test_titles_and_manager_or_technical_labels_do_not_establish_authority():
    analysis = analyze_chapter_seven()
    assert all(item.purchasing_authority is AuthorityStatus.UNKNOWN for item in analysis.stakeholder_map.stakeholders)
    daniel = analysis.stakeholder_map.stakeholders[1]
    maya = analysis.stakeholder_map.stakeholders[0]
    assert daniel.budget_authority is AuthorityStatus.UNKNOWN
    assert maya.technical_authority is AuthorityStatus.UNKNOWN


def test_responsibilities_require_public_evidence_provenance():
    original = analyze_chapter_seven().stakeholder_map.stakeholders[0]
    with pytest.raises(ValueError, match="responsibility requires"):
        replace(original, responsibilities=("Unsupported responsibility",))
    with pytest.raises(ValueError, match="provenance"):
        StakeholderEvidence("bad", "blue-resort", StakeholderClaimType.RESPONSIBILITY, "Claim", "", PublicSourceType.COMPANY_WEBSITE)


def test_evidence_proximity_is_question_and_domain_specific():
    maya = analyze_chapter_seven().stakeholder_map.stakeholders[0]
    assert {item.validation_question for item in maya.question_proximities} == {
        item.validation_question for item in maya.question_proximities
    }
    assert all(item.domain in maya.knowledge_domains for item in maya.question_proximities)
    assert {item.proximity for item in maya.question_proximities} == {EvidenceProximity.DIRECT, EvidenceProximity.NEAR}


def test_knowledge_domains_and_unknown_authority_are_deterministic():
    first = analyze_chapter_seven().stakeholder_map.stakeholders
    second = analyze_chapter_seven().stakeholder_map.stakeholders
    assert tuple(item.knowledge_domains for item in first) == tuple(item.knowledge_domains for item in second)
    assert first[0].knowledge_domains == (KnowledgeDomain.WORKFLOW, KnowledgeDomain.TECHNOLOGY, KnowledgeDomain.OPERATIONS)
    assert all(item.procurement_authority is AuthorityStatus.UNKNOWN for item in first)


def test_executive_seniority_does_not_determine_first_contact():
    analysis = analyze_chapter_seven()
    primary = next(item for item in analysis.priorities if item.priority is ContactPriority.PRIMARY_VALIDATION_CONTACT)
    assert primary.stakeholder_id == "maya"
    assert primary.stakeholder_id != "marcus"
    assert not hasattr(primary, "purchase_probability")


def test_map_preserves_only_supported_relationships_and_explicit_unknowns():
    relationships = analyze_chapter_seven().stakeholder_map.relationships
    known = tuple(item for item in relationships if item.relationship_type is not RelationshipType.UNKNOWN_RELATIONSHIP)
    unknown = tuple(item for item in relationships if item.relationship_type is RelationshipType.UNKNOWN_RELATIONSHIP)
    assert all(item.evidence_ids for item in known)
    assert unknown and all(not item.evidence_ids for item in unknown)


def test_questions_can_map_to_many_people_or_to_unknown():
    mappings = analyze_chapter_seven().stakeholder_map.question_mappings
    coordination = next(item for item in mappings if item.question.startswith("How are reservations"))
    budget = next(item for item in mappings if "budget" in item.question)
    assert coordination.stakeholder_ids == ("maya", "daniel", "sofia")
    assert budget.stakeholder_ids == ()


def test_budget_and_procurement_gaps_do_not_block_initial_conversation():
    coverage = analyze_chapter_seven().coverage
    by_domain = dict(coverage.by_domain)
    assert by_domain[KnowledgeDomain.WORKFLOW] is DomainCoverage.COVERED
    assert by_domain[KnowledgeDomain.TECHNOLOGY] is DomainCoverage.COVERED
    assert by_domain[KnowledgeDomain.BUSINESS_IMPACT] is DomainCoverage.COVERED
    assert by_domain[KnowledgeDomain.FINANCE] is DomainCoverage.UNKNOWN
    assert by_domain[KnowledgeDomain.PROCUREMENT] is DomainCoverage.UNKNOWN
    assert coverage.status is CoverageStatus.COVERAGE_READY


def test_no_champion_outreach_purchase_score_or_hypothesis_validation_is_created():
    analysis = analyze_chapter_seven()
    assert "CHAMPION" not in OrganizationalRole.__members__
    assert analysis.outreach_sent is False
    assert analysis.hypothesis.status is HypothesisStatus.SUPPORTED_FOR_VALIDATION
    assert analysis.hypothesis.status is not HypothesisStatus.VALIDATED
    assert all(not hasattr(item, "purchase_probability") for item in analysis.priorities)


def test_chapter_seven_cli_is_deterministic_and_prior_chapters_still_run(capsys):
    assert chapter_seven_report() == chapter_seven_report()
    for chapter in range(8):
        assert main([f"chapter-{chapter}"]) == 0
        capsys.readouterr()
    assert main(["chapter-7"]) == 0
    first = capsys.readouterr().out
    assert main(["chapter-7"]) == 0
    assert capsys.readouterr().out == first == chapter_seven_report()
    assert "PRIMARY VALIDATION CONTACT\n\nMaya Chen" in first
    assert "PURCHASING AUTHORITY\nUNKNOWN" in first
    assert "OUTREACH SENT\n\nNo." in first
