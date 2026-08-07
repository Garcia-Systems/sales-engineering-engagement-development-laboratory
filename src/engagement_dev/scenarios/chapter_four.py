"""Chapter 4's deterministic, fictional public account research."""

from datetime import date

from engagement_dev.domain import (
    AccountEvidence, AccountInterpretation, AccountResearchBrief,
    CorroboratedObservation, EvidenceCategory, EvidenceConflict, PublicSourceType,
    ResearchClaimType, ResearchDimension, ResearchUnknown, SourceReliability,
)
from engagement_dev.scenarios.chapter_three import load_chapter_three
from engagement_dev.services import AccountResearchEvaluator, classify_freshness


RESEARCH_DATE = date(2026, 8, 1)


def load_chapter_four() -> AccountResearchBrief:
    previous = load_chapter_three()
    account = next(item for item in previous.accounts if item.id == "blue-resort")

    def evidence(identifier, description, source, source_type, reliability, observed_on, dimension,
                 claim_type=ResearchClaimType.OBSERVATION, problems=()):
        return AccountEvidence(
            identifier, account.id, description, EvidenceCategory.PUBLIC_FACT, source, problems, False,
            source_type, reliability, observed_on, dimension, claim_type,
        )

    items = (
        evidence("r1", "Blue Heron Resort operates three properties.", "Blue Heron Resort public website — properties page",
                 PublicSourceType.COMPANY_WEBSITE, SourceReliability.PRIMARY_PUBLIC_SOURCE, date(2026, 7, 20),
                 ResearchDimension.ORGANIZATION, ResearchClaimType.FACT),
        evidence("r2", "Guests can make online reservations.", "Blue Heron Resort public website — reservations page",
                 PublicSourceType.COMPANY_WEBSITE, SourceReliability.PRIMARY_PUBLIC_SOURCE, date(2026, 7, 18),
                 ResearchDimension.OPERATIONS, problems=("SYSTEM_INTEGRATION",)),
        evidence("r3", "Wedding and conference bookings are publicly offered.", "Blue Heron Resort public website — events page",
                 PublicSourceType.COMPANY_WEBSITE, SourceReliability.PRIMARY_PUBLIC_SOURCE, date(2026, 7, 18),
                 ResearchDimension.OPERATIONS, problems=("MANUAL_WORKFLOW",)),
        evidence("r4", "An Operations Systems Coordinator role is advertised.", "Blue Heron Resort public job posting",
                 PublicSourceType.PUBLIC_JOB_POSTING, SourceReliability.PRIMARY_PUBLIC_SOURCE, date(2026, 7, 15),
                 ResearchDimension.PEOPLE, problems=("PROCESS_VISIBILITY",)),
        evidence("r5", "A fourth property is planned.", "Blue Heron Resort expansion press release",
                 PublicSourceType.PRESS_RELEASE, SourceReliability.PRIMARY_PUBLIC_SOURCE, date(2026, 6, 30),
                 ResearchDimension.CHANGE, ResearchClaimType.FACT, ("DATA_SYNCHRONIZATION",)),
        evidence("r6", "Booking coordination was described as partly manual.", "Coastal Business Journal retrospective",
                 PublicSourceType.PUBLIC_NEWS_ARTICLE, SourceReliability.SECONDARY_PUBLIC_SOURCE, date(2024, 2, 10),
                 ResearchDimension.OPERATIONS, problems=("MANUAL_WORKFLOW",)),
        evidence("r7", "A centralized reservation platform has been introduced.", "Blue Heron Resort platform press release",
                 PublicSourceType.PRESS_RELEASE, SourceReliability.PRIMARY_PUBLIC_SOURCE, date(2026, 5, 12),
                 ResearchDimension.TECHNOLOGY, ResearchClaimType.FACT, ("SYSTEM_INTEGRATION",)),
    )
    inferences = (
        AccountInterpretation("ri1", account.id, "Expansion may increase coordination requirements.", ("r1", "r3", "r5")),
        AccountInterpretation("ri2", account.id, "Systems-related hiring may indicate active operational technology work.", ("r4", "r7")),
    )
    unknown_questions = (
        ("u1", "Whether current systems are integrated", ResearchDimension.TECHNOLOGY),
        ("u2", "Whether employees perform duplicate data entry", ResearchDimension.OPERATIONS),
        ("u3", "Whether management considers current workflows problematic", ResearchDimension.OPERATIONS),
        ("u4", "Whether an active project exists", ResearchDimension.CHANGE),
        ("u5", "Whether outside assistance is desired", ResearchDimension.PEOPLE),
        ("u6", "Whether budget exists", ResearchDimension.ORGANIZATION),
    )
    return AccountResearchBrief(
        account, previous.selected_market, RESEARCH_DATE, items, inferences,
        tuple(ResearchUnknown(i, account.id, question, dimension) for i, question, dimension in unknown_questions),
        (EvidenceConflict("c1", account.id, ("r6", "r7"),
                          "The stale historical manual-coordination report and current platform announcement are both retained; the newer primary source changes the current interpretation.", False),),
        (CorroboratedObservation(
            "Public evidence shows multi-property operations undergoing change.", ("r1", "r4", "r5", "r7"),
            "Independent public pages strengthen research interest but do not establish customer pain.",
        ),),
        ("PROCESS_VISIBILITY", "SYSTEM_INTEGRATION", "MANUAL_WORKFLOW", "DATA_SYNCHRONIZATION"),
    )


def evaluate_chapter_four():
    return AccountResearchEvaluator().evaluate(load_chapter_four())


def chapter_four_report() -> str:
    brief = load_chapter_four()
    result = evaluate_chapter_four()
    lines = [
        "CHAPTER 4 — RESEARCHING AN ACCOUNT", "", "ACCOUNT RESEARCH BRIEF", "", "ACCOUNT", brief.account.name,
        "", "MARKET", brief.market.name, "", "RESEARCH DATE", brief.research_date.isoformat(), "", "PUBLIC SOURCES",
    ]
    for item in brief.evidence:
        lines.extend((f"- {item.source}", f"  Type: {item.source_type}", f"  Reliability: {item.source_reliability}"))
    for dimension in ResearchDimension:
        evidence = tuple(item for item in brief.evidence if item.dimension is dimension)
        if evidence:
            lines.extend(("", dimension.value, "", "KNOWN / OBSERVED"))
            for item in evidence:
                lines.extend((f"* [{item.claim_type}] {item.description}",
                              f"  Evidence: {item.id} | Freshness: {classify_freshness(item.observed_on, brief.research_date)}"))
    lines.extend(("", "INFERENCES"))
    lines.extend(f"* {item.statement} (evidence: {', '.join(item.evidence_ids)})" for item in brief.inferences)
    lines.extend(("", "CORROBORATION"))
    for item in brief.corroborated_observations:
        lines.extend((f"* {item.statement}", f"  Evidence: {', '.join(item.evidence_ids)}", f"  Limit: {item.explanation}"))
    lines.extend(("", "CONFLICTING EVIDENCE"))
    for item in brief.conflicts:
        lines.extend((f"* {', '.join(item.evidence_ids)}", f"  {item.explanation}", "  Preserved for review: YES"))
    lines.extend(("", "UNKNOWNS"))
    lines.extend(f"* {item.question}" for item in brief.unknowns)
    lines.extend(("", "IMPORTANT", "No customer problem has been established.", "PUBLIC EVIDENCE ≠ CUSTOMER CONFIRMATION",
                  "", "RESEARCH STATUS", "", result.status.value, "", "WHY"))
    lines.extend(f"* {reason}" for reason in result.reasons)
    lines.extend(("* Technology observations recorded", "* Change activity observed", "", "STOPPING RULE",
                  "Stop broad account research: YES — enough evidence identifies specific observations worth signal analysis.",
                  "Additional public research is not currently expected to materially improve the broad brief.",
                  "", "OPPORTUNITY STATUS", "", "No opportunity hypothesis created.",
                  "No engagement candidate created.", "", "NEXT STEP",
                  "Analyze the research brief for observable signals that may justify a specific opportunity hypothesis."))
    return "\n".join(lines) + "\n"
