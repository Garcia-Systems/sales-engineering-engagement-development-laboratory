"""Chapter 3's fictional organizations and deterministic account research queue."""

from dataclasses import dataclass

from engagement_dev.domain import (
    Account, AccountEvidence, AccountInterpretation, EvidenceCategory,
    Market, MarketCharacteristic, ServiceOffer,
)
from engagement_dev.scenarios.chapter_two import load_chapter_two
from engagement_dev.services import (
    AccountListBuilder, AccountResearchQueue, AccountSelectionStatus,
)


@dataclass(frozen=True)
class ChapterThreeData:
    selected_market: Market
    supported_offer: ServiceOffer
    market_characteristics: tuple[MarketCharacteristic, ...]
    accounts: tuple[Account, ...]
    evidence: tuple[AccountEvidence, ...]
    interpretations: tuple[AccountInterpretation, ...]
    research_capacity: int


def load_chapter_three() -> ChapterThreeData:
    chapter_two = load_chapter_two()
    market_candidate = chapter_two.candidates[0]
    accounts = (
        Account("blue-resort", "Blue Heron Resort", "hospitality", "Independent resort group", "Fictional Coastal Region", "Three-property hospitality operator."),
        Account("colonial-hotel", "Colonial Harbor Hotel", "hospitality", "Independent hotel", "Fictional Harbor District", "Hotel with dining and event services."),
        Account("seaside-suites", "Seaside Conference Suites", "hospitality", "Conference hotel", "Fictional Coastal Region", "Lodging and conference operator."),
        Account("harborview", "Harborview Flagged Hotel", "hospitality", "Franchised hotel", "Fictional Harbor District", "Property operating under a centralized brand platform."),
        Account("tidewater-inn", "Tidewater Inn", "hospitality", "Small independent inn", "Fictional Peninsula", "Small property with a simple operating model."),
        Account("heritage", "Heritage Lodging Group", "hospitality", "Lodging company", "Fictional Coastal Region", "Public listing identifies a lodging company."),
        Account("sandpiper", "Sandpiper Guest House", "hospitality", "Guest house", "Fictional Peninsula", "Limited public description."),
        Account("peninsula-controls", "Peninsula Industrial Controls", "industrial", "Industrial controls engineering", "Fictional Peninsula", "Specialized control-systems company."),
    )

    def e(identifier: str, account: str, description: str, source: str, problems: tuple[str, ...] = (), *, negative: bool = False) -> AccountEvidence:
        return AccountEvidence(identifier, account, description, EvidenceCategory.PUBLIC_FACT, source, problems, negative)

    evidence = (
        e("br-1", "blue-resort", "Operates multiple properties", "Fictional company website — properties page", ("PROCESS_VISIBILITY",)),
        e("br-2", "blue-resort", "Offers online reservations and event operations", "Fictional company website — booking page", ("SYSTEM_INTEGRATION",)),
        e("br-3", "blue-resort", "Publicly describes staff scheduling across properties", "Fictional careers page", ("MANUAL_WORKFLOW",)),
        e("br-4", "blue-resort", "Recent expansion announcement adds a third property", "Fictional regional business announcement", ("DATA_SYNCHRONIZATION",)),
        e("ch-1", "colonial-hotel", "Uses multiple public reservation channels", "Fictional hotel booking page", ("SYSTEM_INTEGRATION",)),
        e("ch-2", "colonial-hotel", "Operates a restaurant and accepts event bookings", "Fictional hotel services page", ("MANUAL_WORKFLOW",)),
        e("ch-3", "colonial-hotel", "Publicly describes a guest messaging system", "Fictional guest information page", ("PROCESS_VISIBILITY",)),
        e("ss-1", "seaside-suites", "Hosts lodging, conferences, and catered events", "Fictional services brochure", ("MANUAL_WORKFLOW",)),
        e("ss-2", "seaside-suites", "Uses separate public room and event inquiry workflows", "Fictional reservations page", ("SYSTEM_INTEGRATION",)),
        e("ss-3", "seaside-suites", "Recent renovation added two event spaces", "Fictional renovation announcement", ("PROCESS_VISIBILITY",)),
        e("hf-1", "harborview", "Uses a long-term centralized corporate technology platform", "Fictional franchise technology notice", ("SYSTEM_INTEGRATION",), negative=True),
        e("hf-2", "harborview", "Local property has no discretion over platform changes", "Fictional franchise operations notice", ("SYSTEM_INTEGRATION",), negative=True),
        e("ti-1", "tidewater-inn", "Accepts direct and regional tourism-site reservations", "Fictional tourism directory", ("SYSTEM_INTEGRATION",)),
        e("ti-2", "tidewater-inn", "Publishes a small event-request workflow", "Fictional inn website", ("MANUAL_WORKFLOW",)),
        e("he-1", "heritage", "Identifies itself as a regional lodging organization", "Fictional public business directory"),
        e("pc-1", "peninsula-controls", "Designs specialized industrial control systems", "Fictional company capabilities page", ("SYSTEM_INTEGRATION",)),
    )
    interpretations = (
        AccountInterpretation("i-br", "blue-resort", "Multiple operations and recent change may make workflow and integration questions worth researching.", ("br-1", "br-2", "br-3", "br-4")),
        AccountInterpretation("i-ch", "colonial-hotel", "Multiple public operational workflows may warrant deeper research.", ("ch-1", "ch-2", "ch-3")),
        AccountInterpretation("i-ss", "seaside-suites", "Expanded event operations may warrant research into cross-workflow coordination.", ("ss-1", "ss-2", "ss-3")),
        AccountInterpretation("i-hf", "harborview", "Centralized control may make this local account inappropriate for the current investigation.", ("hf-1", "hf-2")),
        AccountInterpretation("i-ti", "tidewater-inn", "Two observable workflows provide a modest reason for research if capacity permits.", ("ti-1", "ti-2")),
    )
    return ChapterThreeData(
        market_candidate.market, chapter_two.supported_offer, market_candidate.characteristics,
        accounts, evidence, interpretations, 3,
    )


def build_chapter_three_queue() -> AccountResearchQueue:
    data = load_chapter_three()
    return AccountListBuilder().build(
        selected_market=data.selected_market, supported_offer=data.supported_offer,
        market_characteristics=data.market_characteristics, accounts=data.accounts,
        evidence=data.evidence, interpretations=data.interpretations,
        research_capacity=data.research_capacity,
    )


def chapter_three_report() -> str:
    data = load_chapter_three()
    queue = build_chapter_three_queue()
    accounts = {item.id: item for item in data.accounts}
    lines = [
        "CHAPTER 3 — BUILDING AN ACCOUNT LIST", "", "SELECTED MARKET", data.selected_market.name,
        "", "SUPPORTED OFFER", data.supported_offer.statement, "", "ACCOUNT RESEARCH QUEUE",
    ]
    for index, result in enumerate(queue.selected, 1):
        candidate = result.candidate
        assert candidate is not None
        lines.extend(("", f"{index}. {candidate.account.name}", f"    Status: {result.status}", "    Evidence:"))
        lines.extend(f"    * {item.description} — {item.source}" for item in candidate.supporting_evidence)
        lines.extend(("    Interpretation:", f"    {result.interpretations[0].statement}", "    Research rationale:",
                      f"    {candidate.research_rationale}", "    Important:", "    No customer problem has been established."))

    for status, heading in (
        (AccountSelectionStatus.DEFERRED, "DEFERRED"),
        (AccountSelectionStatus.INSUFFICIENT_EVIDENCE, "INSUFFICIENT EVIDENCE"),
        (AccountSelectionStatus.OUTSIDE_SELECTED_MARKET, "OUTSIDE SCOPE"),
        (AccountSelectionStatus.OUTSIDE_SUPPORTED_OFFER, "OUTSIDE SUPPORTED OFFER"),
    ):
        items = tuple(item for item in queue.evaluations if item.status is status)
        if items:
            lines.extend(("", heading))
            for item in items:
                lines.extend(("", accounts[item.account_id].name, "Reason:", item.reason))

    counts = {status: sum(item.status is status for item in queue.evaluations) for status in AccountSelectionStatus}
    lines.extend((
        "", "ACCOUNT LIST STATUS", "", f"Candidate accounts: {len(data.accounts)}",
        f"Selected for deep research: {counts[AccountSelectionStatus.SELECTED_FOR_RESEARCH]}",
        f"Deferred: {counts[AccountSelectionStatus.DEFERRED]}",
        f"Insufficient evidence: {counts[AccountSelectionStatus.INSUFFICIENT_EVIDENCE]}",
        f"Outside scope: {counts[AccountSelectionStatus.OUTSIDE_SELECTED_MARKET] + counts[AccountSelectionStatus.OUTSIDE_SUPPORTED_OFFER]}",
        "", "Qualified opportunities: 0", "", "An account list is a research queue, not a sales pipeline.",
        "No opportunity hypothesis or engagement candidate has been created.", "", "NEXT STEP",
        "Research the selected accounts for specific observable signals.", "This prepares Chapter 4.",
    ))
    return "\n".join(lines) + "\n"
