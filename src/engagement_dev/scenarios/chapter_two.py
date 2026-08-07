"""Chapter 2's fictional candidate markets and deterministic research cycle."""

from dataclasses import dataclass

from engagement_dev.domain import (
    CapabilityProfile, EvidenceCategory, Market, MarketCharacteristic, MarketEvidence,
    ServiceOffer,
)
from engagement_dev.scenarios.chapter_one import BOUNDARIES, PROBLEM_CLASSES, load_chapter_one
from engagement_dev.services import MarketEvaluation, MarketEvaluator, ResearchCycle


@dataclass(frozen=True)
class CandidateMarket:
    market: Market
    characteristics: tuple[MarketCharacteristic, ...]
    evidence: tuple[MarketEvidence, ...]
    excluded_boundary_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class ChapterTwoData:
    profile: CapabilityProfile
    supported_offer: ServiceOffer
    candidates: tuple[CandidateMarket, ...]
    research_capacity: int


def _candidate(
    identifier: str, name: str, patterns: tuple[tuple[str, tuple[str, ...]], ...],
    *, weak: bool = False, boundary: tuple[str, ...] = (),
) -> CandidateMarket:
    market = Market(identifier, name, (), f"Fictional candidate market: {name}.")
    evidence = tuple(
        MarketEvidence(
            f"{identifier}-e{index}", identifier, description,
            EvidenceCategory.INFERENCE if weak else (
                EvidenceCategory.INDUSTRY_PATTERN if index % 2 else EvidenceCategory.OBSERVED_TECHNOLOGY_PATTERN
            ),
            "Fictional deterministic market research",
        )
        for index, (description, _) in enumerate(patterns, 1)
    )
    characteristics = tuple(
        MarketCharacteristic(
            f"{identifier}-c{index}", identifier, description, problem_ids,
            (f"{identifier}-e{index}",),
        )
        for index, (description, problem_ids) in enumerate(patterns, 1)
    )
    return CandidateMarket(market, characteristics, evidence, boundary)


def load_chapter_two() -> ChapterTwoData:
    chapter_one = load_chapter_one()
    supported_offer = ServiceOffer(
        "chapter-2-supported-offer",
        "We investigate operational workflows involving disconnected systems, repeated information transfer, synchronization problems, and manual handoffs.",
        ("api", "data", "automation", "web", "prototype"),
        tuple(PROBLEM_CLASSES[item] for item in (
            "SYSTEM_INTEGRATION", "MANUAL_WORKFLOW", "DATA_SYNCHRONIZATION", "PROCESS_VISIBILITY"
        )),
        ("inventory-lab", "workflow-prototype"),
        BOUNDARIES,
    )
    candidates = (
        _candidate("hospitality", "Regional Hospitality", (
            ("Multiple reservation, payment, and customer communication systems", ("SYSTEM_INTEGRATION",)),
            ("Scheduling, housekeeping, and repeated operational handoffs", ("MANUAL_WORKFLOW", "PROCESS_VISIBILITY")),
        )),
        _candidate("retail", "Independent Retail & Specialty Stores", (
            ("Point-of-sale, inventory, e-commerce, and supplier systems", ("SYSTEM_INTEGRATION", "DATA_SYNCHRONIZATION")),
            ("Repeated inventory and customer-information transfers", ("MANUAL_WORKFLOW",)),
        )),
        _candidate("professional", "Professional Services", (
            ("Document, scheduling, billing, and customer-intake workflows", ("MANUAL_WORKFLOW",)),
        )),
        _candidate("industrial", "Industrial Control Engineering", (
            ("Complex control systems with specialized integration requirements", ("SYSTEM_INTEGRATION",)),
            ("Legacy and new control technology coexist", ("DATA_SYNCHRONIZATION",)),
        ), boundary=("no-security-audit",)),
        _candidate("weak", "Example Weak-Evidence Market", (
            ("Organizations might transfer information manually", ("MANUAL_WORKFLOW",)),
        ), weak=True),
    )
    return ChapterTwoData(chapter_one.profile, supported_offer, candidates, 2)


def evaluate_chapter_two() -> tuple[tuple[CandidateMarket, MarketEvaluation], ...]:
    data = load_chapter_two()
    evaluator = MarketEvaluator()
    return tuple((candidate, evaluator.evaluate(
        supported_offer=data.supported_offer, profile=data.profile, market=candidate.market,
        characteristics=candidate.characteristics, evidence=candidate.evidence,
        excluded_boundary_ids=candidate.excluded_boundary_ids,
    )) for candidate in data.candidates)


def chapter_two_research_cycle() -> ResearchCycle:
    data = load_chapter_two()
    return MarketEvaluator().allocate(tuple(result for _, result in evaluate_chapter_two()), data.research_capacity)


def chapter_two_report() -> str:
    data = load_chapter_two()
    evaluated = evaluate_chapter_two()
    lines = ["CHAPTER 2 — CHOOSING A MARKET", "", "SUPPORTED OFFER", data.supported_offer.statement]
    for candidate, result in evaluated:
        lines.extend(("", "⸻", "", "MARKET", candidate.market.name, "", "OBSERVED CHARACTERISTICS"))
        lines.extend(f"* {item.description}" for item in candidate.characteristics)
        lines.extend(("", "EVIDENCE"))
        observed = tuple(item for item in candidate.evidence if item.is_observed)
        lines.extend(f"* [{item.category}] {item.description} — {item.source}" for item in observed)
        if not observed:
            lines.append("Insufficient.")
        if result.relevant_problem_class_ids:
            lines.extend(("", "RELEVANT PROBLEM CLASSES"))
            lines.extend(f"* {item}" for item in result.relevant_problem_class_ids)
        if candidate.excluded_boundary_ids:
            lines.extend(("", "BOUNDARY"))
            lines.extend(f"* {finding}" for finding in result.findings)
        if result.hypothesis:
            lines.extend(("", "MARKET HYPOTHESIS", result.hypothesis.cautious_statement))
        lines.extend(("", "IMPORTANT", "This does not establish that any individual organization has these problems.",
                      "", "EVALUATION", result.priority))

    cycle = chapter_two_research_cycle()
    names = {candidate.market.id: candidate.market.name for candidate in data.candidates}
    lines.extend(("", "⸻", "", "RESEARCH CYCLE", f"Available deep-research slots: {cycle.capacity}", "", "Selected:"))
    lines.extend(f"{index}. {names[item]}" for index, item in enumerate(cycle.selected_market_ids, 1))
    lines.extend(("", "Deferred:"))
    lines.extend(f"* {names[item]}" for item in cycle.deferred_market_ids)
    lines.extend(("", "Rejected:"))
    lines.extend(f"* {names[item]}" for item in cycle.rejected_market_ids)
    lines.extend(("", "Insufficient evidence:"))
    lines.extend(f"* {names[item]}" for item in cycle.insufficient_evidence_market_ids)
    lines.extend(("", "Deferred does not mean bad; it means not selected given current evidence and capacity.",
                  "A market research priority is not proof of customer need, guaranteed revenue, or a qualified opportunity.",
                  "", "NEXT", "Selected Market → Account Research"))
    return "\n".join(lines) + "\n"
