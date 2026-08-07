"""Chapter 7: map evidence sources without inferring buyers or sending outreach."""

from dataclasses import dataclass

from engagement_dev.domain import (
    AuthorityStatus, Contact, EvidenceProximity, KnowledgeDomain, OrganizationalRole,
    PublicSourceType, QuestionProximity, RelationshipType, Stakeholder,
    StakeholderClaimType, StakeholderEvidence, StakeholderMap,
    StakeholderRelationship, ValidationQuestionMapping,
)
from engagement_dev.scenarios.chapter_six import analyze_chapter_six
from engagement_dev.services import (
    ContactPriorityDecision, CoverageStatus, StakeholderMapper, ValidationCoverage,
)


@dataclass(frozen=True)
class ChapterSevenAnalysis:
    hypothesis: object
    stakeholder_map: StakeholderMap
    coverage: ValidationCoverage
    priorities: tuple[ContactPriorityDecision, ...]
    outreach_sent: bool = False


def _evidence(identifier: str, claim_type: StakeholderClaimType, claim: str, source: str, source_type: PublicSourceType) -> StakeholderEvidence:
    return StakeholderEvidence(identifier, "blue-resort", claim_type, claim, source, source_type)


def analyze_chapter_seven() -> ChapterSevenAnalysis:
    chapter_six = analyze_chapter_six()
    hypothesis = chapter_six.candidates[0].hypothesis
    questions = hypothesis.validation_questions
    coordination, role_prompt, cross_property = questions[2], questions[3], questions[1]
    changing, difficult, improved, working_well = questions[0], questions[4], questions[5], questions[6]

    maya_evidence = (
        _evidence("se-maya-title", StakeholderClaimType.TITLE, "Operations Systems Coordinator", "Fictional Blue Heron public job posting", PublicSourceType.PUBLIC_JOB_POSTING),
        _evidence("se-maya-resp", StakeholderClaimType.RESPONSIBILITY, "Operational systems coordination across properties", "Fictional Blue Heron public job posting", PublicSourceType.PUBLIC_JOB_POSTING),
        _evidence("se-maya-role", StakeholderClaimType.ORGANIZATIONAL_ROLE, "Coordinates operational systems", "Fictional Blue Heron public job posting", PublicSourceType.PUBLIC_JOB_POSTING),
    )
    daniel_evidence = (
        _evidence("se-daniel-title", StakeholderClaimType.TITLE, "Director of Operations", "Fictional Blue Heron leadership page", PublicSourceType.COMPANY_WEBSITE),
        _evidence("se-daniel-resp", StakeholderClaimType.RESPONSIBILITY, "Oversight of property operations", "Fictional Blue Heron leadership page", PublicSourceType.COMPANY_WEBSITE),
        _evidence("se-daniel-role", StakeholderClaimType.ORGANIZATIONAL_ROLE, "Operational workflow and business stakeholder", "Fictional Blue Heron leadership page", PublicSourceType.COMPANY_WEBSITE),
        _evidence("se-daniel-maya", StakeholderClaimType.RELATIONSHIP, "Works with the Operations Systems Coordinator", "Fictional Blue Heron organizational chart", PublicSourceType.COMPANY_WEBSITE),
    )
    sofia_evidence = (
        _evidence("se-sofia-title", StakeholderClaimType.TITLE, "Events Manager", "Fictional Blue Heron conference biography", PublicSourceType.PUBLIC_DIRECTORY),
        _evidence("se-sofia-resp", StakeholderClaimType.RESPONSIBILITY, "Conference and wedding operations", "Fictional Blue Heron conference biography", PublicSourceType.PUBLIC_DIRECTORY),
        _evidence("se-sofia-role", StakeholderClaimType.ORGANIZATIONAL_ROLE, "Event workflow owner", "Fictional Blue Heron conference biography", PublicSourceType.PUBLIC_DIRECTORY),
        _evidence("se-sofia-ops", StakeholderClaimType.RELATIONSHIP, "Works with property operations", "Fictional Blue Heron events page", PublicSourceType.COMPANY_WEBSITE),
    )
    marcus_evidence = (
        _evidence("se-marcus-title", StakeholderClaimType.TITLE, "General Manager", "Fictional Blue Heron leadership page", PublicSourceType.COMPANY_WEBSITE),
        _evidence("se-marcus-resp", StakeholderClaimType.RESPONSIBILITY, "General management and operating strategy", "Fictional Blue Heron leadership page", PublicSourceType.COMPANY_WEBSITE),
        _evidence("se-marcus-role", StakeholderClaimType.ORGANIZATIONAL_ROLE, "Business stakeholder", "Fictional Blue Heron leadership page", PublicSourceType.COMPANY_WEBSITE),
        _evidence("se-marcus-daniel", StakeholderClaimType.RELATIONSHIP, "Oversees the Director of Operations", "Fictional Blue Heron organizational chart", PublicSourceType.COMPANY_WEBSITE),
    )
    priya_evidence = (
        _evidence("se-priya-title", StakeholderClaimType.TITLE, "Marketing Manager", "Fictional Blue Heron public professional profile", PublicSourceType.PUBLIC_DIRECTORY),
        _evidence("se-priya-resp", StakeholderClaimType.RESPONSIBILITY, "Guest marketing and customer communications", "Fictional Blue Heron public professional profile", PublicSourceType.PUBLIC_DIRECTORY),
        _evidence("se-priya-role", StakeholderClaimType.ORGANIZATIONAL_ROLE, "Customer-experience influencer", "Fictional Blue Heron public professional profile", PublicSourceType.PUBLIC_DIRECTORY),
    )
    stakeholders = (
        Stakeholder(Contact("maya", "blue-resort", "Maya Chen", "Operations Systems Coordinator"), "blue-resort", "Operations Systems Coordinator", (OrganizationalRole.WORKFLOW_OWNER, OrganizationalRole.TECHNICAL_STAKEHOLDER), ("Operational systems coordination across properties",), (KnowledgeDomain.WORKFLOW, KnowledgeDomain.TECHNOLOGY, KnowledgeDomain.OPERATIONS), (
            QuestionProximity(coordination, KnowledgeDomain.WORKFLOW, EvidenceProximity.DIRECT), QuestionProximity(role_prompt, KnowledgeDomain.OPERATIONS, EvidenceProximity.DIRECT), QuestionProximity(cross_property, KnowledgeDomain.WORKFLOW, EvidenceProximity.DIRECT), QuestionProximity(changing, KnowledgeDomain.OPERATIONS, EvidenceProximity.NEAR), QuestionProximity(difficult, KnowledgeDomain.WORKFLOW, EvidenceProximity.DIRECT), QuestionProximity(improved, KnowledgeDomain.TECHNOLOGY, EvidenceProximity.DIRECT), QuestionProximity(working_well, KnowledgeDomain.WORKFLOW, EvidenceProximity.DIRECT),
        ), "Close to systems coordination questions; purchasing status is not established.", maya_evidence),
        Stakeholder(Contact("daniel", "blue-resort", "Daniel Brooks", "Director of Operations"), "blue-resort", "Director of Operations", (OrganizationalRole.BUSINESS_STAKEHOLDER, OrganizationalRole.WORKFLOW_OWNER), ("Oversight of property operations",), (KnowledgeDomain.OPERATIONS, KnowledgeDomain.WORKFLOW, KnowledgeDomain.BUSINESS_IMPACT), (
            QuestionProximity(coordination, KnowledgeDomain.OPERATIONS, EvidenceProximity.NEAR), QuestionProximity(role_prompt, KnowledgeDomain.OPERATIONS, EvidenceProximity.DIRECT), QuestionProximity(changing, KnowledgeDomain.BUSINESS_IMPACT, EvidenceProximity.DIRECT), QuestionProximity(difficult, KnowledgeDomain.OPERATIONS, EvidenceProximity.NEAR),
        ), "May connect workflow changes to operational effects; authority remains unknown.", daniel_evidence),
        Stakeholder(Contact("sofia", "blue-resort", "Sofia Ramirez", "Events Manager"), "blue-resort", "Events Manager", (OrganizationalRole.WORKFLOW_OWNER,), ("Conference and wedding operations",), (KnowledgeDomain.WORKFLOW, KnowledgeDomain.CUSTOMER_EXPERIENCE, KnowledgeDomain.OPERATIONS), (
            QuestionProximity(coordination, KnowledgeDomain.WORKFLOW, EvidenceProximity.DIRECT), QuestionProximity(difficult, KnowledgeDomain.WORKFLOW, EvidenceProximity.DIRECT), QuestionProximity(working_well, KnowledgeDomain.CUSTOMER_EXPERIENCE, EvidenceProximity.DIRECT),
        ), "Close to event workflow evidence, not automatically a decision-maker.", sofia_evidence),
        Stakeholder(Contact("marcus", "blue-resort", "Marcus Lee", "General Manager"), "blue-resort", "General Manager", (OrganizationalRole.BUSINESS_STAKEHOLDER,), ("General management and operating strategy",), (KnowledgeDomain.BUSINESS_IMPACT, KnowledgeDomain.STRATEGY, KnowledgeDomain.OPERATIONS), (
            QuestionProximity(changing, KnowledgeDomain.STRATEGY, EvidenceProximity.NEAR), QuestionProximity(difficult, KnowledgeDomain.BUSINESS_IMPACT, EvidenceProximity.NEAR), QuestionProximity(coordination, KnowledgeDomain.WORKFLOW, EvidenceProximity.INDIRECT),
        ), "Close to business impact, but detailed technical knowledge is unknown.", marcus_evidence),
        Stakeholder(Contact("priya", "blue-resort", "Priya Shah", "Marketing Manager"), "blue-resort", "Marketing Manager", (OrganizationalRole.INFLUENCER,), ("Guest marketing and customer communications",), (KnowledgeDomain.CUSTOMER_EXPERIENCE, KnowledgeDomain.MARKETING), (
            QuestionProximity(coordination, KnowledgeDomain.CUSTOMER_EXPERIENCE, EvidenceProximity.INDIRECT),
        ), "May inform customer experience, but is indirect for the current operational-systems hypothesis.", priya_evidence),
    )
    mappings = (
        ValidationQuestionMapping(changing, (KnowledgeDomain.OPERATIONS,), ("maya", "daniel", "marcus")),
        ValidationQuestionMapping(cross_property, (KnowledgeDomain.WORKFLOW,), ("maya", "daniel", "sofia")),
        ValidationQuestionMapping(coordination, (KnowledgeDomain.WORKFLOW, KnowledgeDomain.TECHNOLOGY), ("maya", "daniel", "sofia")),
        ValidationQuestionMapping(role_prompt, (KnowledgeDomain.OPERATIONS,), ("daniel", "maya")),
        ValidationQuestionMapping(difficult, (KnowledgeDomain.WORKFLOW, KnowledgeDomain.BUSINESS_IMPACT), ("maya", "daniel", "sofia", "marcus")),
        ValidationQuestionMapping(improved, (KnowledgeDomain.TECHNOLOGY,), ("maya",)),
        ValidationQuestionMapping(working_well, (KnowledgeDomain.WORKFLOW, KnowledgeDomain.CUSTOMER_EXPERIENCE), ("maya", "sofia")),
        ValidationQuestionMapping("Is there budget for a project?", (KnowledgeDomain.FINANCE,), ()),
    )
    relationships = (
        StakeholderRelationship("marcus", "daniel", RelationshipType.OVERSEES, ("se-marcus-daniel",)),
        StakeholderRelationship("daniel", "maya", RelationshipType.WORKS_WITH, ("se-daniel-maya",)),
        StakeholderRelationship("sofia", "daniel", RelationshipType.WORKS_WITH, ("se-sofia-ops",)),
        StakeholderRelationship("priya", "maya", RelationshipType.UNKNOWN_RELATIONSHIP),
    )
    mapper = StakeholderMapper()
    stakeholder_map = mapper.build(account_id="blue-resort", hypothesis_id=hypothesis.id, stakeholders=stakeholders, relationships=relationships, question_mappings=mappings)
    coverage = mapper.evaluate_coverage(stakeholder_map, (KnowledgeDomain.WORKFLOW, KnowledgeDomain.TECHNOLOGY, KnowledgeDomain.BUSINESS_IMPACT, KnowledgeDomain.FINANCE, KnowledgeDomain.PROCUREMENT))
    return ChapterSevenAnalysis(hypothesis, stakeholder_map, coverage, mapper.prioritize(stakeholder_map))


def chapter_seven_report() -> str:
    analysis = analyze_chapter_seven()
    lines = ["CHAPTER 7 — MAPPING THE BUYING ORGANIZATION", "", "ACCOUNT", "Blue Heron Resort", "", "HYPOTHESIS", analysis.hypothesis.cautious_statement, "", "STATUS", analysis.hypothesis.status.value]
    for stakeholder in analysis.stakeholder_map.stakeholders:
        proximity = stakeholder.question_proximities[0].proximity.value if stakeholder.question_proximities else EvidenceProximity.UNKNOWN.value
        lines += ["", "---", "", "STAKEHOLDER", "", stakeholder.contact.name, stakeholder.title, "", "KNOWN RESPONSIBILITIES", *[f"- {item}" for item in stakeholder.responsibilities], "", "KNOWLEDGE DOMAINS", *[f"- {item.value}" for item in stakeholder.knowledge_domains], "", "EVIDENCE PROXIMITY", proximity, "", "PURCHASING AUTHORITY", stakeholder.purchasing_authority.value, "", "SOURCE PROVENANCE", *[f"- {item.claim_type.value}: {item.source}" for item in stakeholder.evidence]]
    lines += ["", "---", "", "VALIDATION QUESTION MAPPING"]
    names = {item.contact.id: item.contact.name for item in analysis.stakeholder_map.stakeholders}
    for mapping in analysis.stakeholder_map.question_mappings:
        sources = ", ".join(names[item] for item in mapping.stakeholder_ids) or "UNKNOWN"
        lines += ["", "QUESTION", mapping.question, "EVIDENCE SOURCES", sources]
    lines += ["", "VALIDATION COVERAGE"]
    for domain, status in analysis.coverage.by_domain:
        lines += ["", f"{domain.value.replace('_', ' ').title()}:", status.value]
    lines += ["", "STATUS:", "COVERAGE_READY_FOR_INITIAL_CONVERSATION" if analysis.coverage.status is CoverageStatus.COVERAGE_READY else analysis.coverage.status.value]
    primary = next(item for item in analysis.priorities if item.priority.value == "PRIMARY_VALIDATION_CONTACT")
    lines += ["", "---", "", "PRIMARY VALIDATION CONTACT", "", names[primary.stakeholder_id], "", "WHY", "", primary.rationale, "", "IMPORTANT", "", "This does not establish that this person is:", "- a buyer", "- a champion", "- a budget owner", "- a decision-maker", "", "This priority identifies an evidence source, not purchase probability.", "Organizational seniority and evidence proximity are different dimensions.", "The opportunity hypothesis remains provisional and has not been validated.", "", "OUTREACH SENT", "", "No."]
    return "\n".join(lines) + "\n"
