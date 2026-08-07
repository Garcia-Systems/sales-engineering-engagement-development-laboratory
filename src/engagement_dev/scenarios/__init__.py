"""Deterministic teaching scenarios."""

from dataclasses import dataclass

from engagement_dev.domain import Account, EvidenceCategory, Market, ObservedSignal
from engagement_dev.scenarios.chapter_one import chapter_one_report, evaluate_chapter_one, load_chapter_one
from engagement_dev.scenarios.chapter_two import (
    chapter_two_report, chapter_two_research_cycle, evaluate_chapter_two, load_chapter_two,
)
from engagement_dev.scenarios.chapter_three import (
    build_chapter_three_queue, chapter_three_report, load_chapter_three,
)
from engagement_dev.scenarios.chapter_four import (
    chapter_four_report, evaluate_chapter_four, load_chapter_four,
)
from engagement_dev.scenarios.chapter_five import analyze_chapter_five, chapter_five_report
from engagement_dev.scenarios.chapter_six import analyze_chapter_six, chapter_six_report
from engagement_dev.scenarios.chapter_seven import analyze_chapter_seven, chapter_seven_report
from engagement_dev.scenarios.chapter_eight import analyze_chapter_eight, chapter_eight_report
from engagement_dev.scenarios.chapter_nine import analyze_chapter_nine, chapter_nine_report
from engagement_dev.scenarios.chapter_ten import analyze_chapter_ten, chapter_ten_report
from engagement_dev.scenarios.chapter_eleven import analyze_chapter_eleven, chapter_eleven_report
from engagement_dev.services import create_hypothesis


@dataclass(frozen=True)
class ChapterZeroData:
    market: Market
    accounts: tuple[Account, ...]
    signals: tuple[ObservedSignal, ...]


def load_chapter_zero() -> ChapterZeroData:
    """Return a fixed fictional regional market; no network or external API is used."""
    account_names = (
        ("harbor", "Harbor Street Music"),
        ("colonial", "Colonial Community Bank"),
        ("tidewater", "Tidewater Manufacturing"),
        ("peninsula", "Peninsula Home Services"),
        ("blue-heron", "Blue Heron Hospitality"),
    )
    accounts = tuple(Account(key, name, "coastal-region") for key, name in account_names)
    market = Market("coastal-region", "Fictional Coastal Regional Market", tuple(a.id for a in accounts))
    signals = (
        ObservedSignal("s1", "harbor", "Hiring for e-commerce operations", EvidenceCategory.PUBLIC_FACT, "Fictional public job listing"),
        ObservedSignal("s2", "harbor", "Recent website platform migration", EvidenceCategory.OBSERVED_BEHAVIOR, "Fictional website change log"),
        ObservedSignal("s3", "colonial", "Published a digital banking modernization program", EvidenceCategory.PUBLIC_FACT, "Fictional annual report"),
        ObservedSignal("s4", "tidewater", "Expanded a production facility", EvidenceCategory.PUBLIC_FACT, "Fictional permit record"),
        ObservedSignal("s5", "tidewater", "Expansion may create integration pressure", EvidenceCategory.INFERENCE, "Analyst interpretation"),
        ObservedSignal("s6", "peninsula", "Redesigned its public logo", EvidenceCategory.OBSERVED_BEHAVIOR, "Fictional public website"),
    )
    return ChapterZeroData(market, accounts, signals)


HYPOTHESES = {
    "harbor": "Available evidence supports investigating whether an operational integration problem exists.",
    "colonial": "Available evidence supports investigating the technical scope of the modernization program.",
}


def chapter_zero_report() -> str:
    data = load_chapter_zero()
    lines = [f"MARKET: {data.market.name}", ""]
    for account in data.accounts:
        evidence = tuple(s for s in data.signals if s.account_id == account.id)
        lines.extend((f"ACCOUNT: {account.name}", "Observed signals:"))
        if evidence:
            lines.extend(f"- [{s.category}] {s.description}" for s in evidence)
        else:
            lines.append("- None relevant to current capability profile")
        statement = HYPOTHESES.get(account.id)
        if statement:
            hypothesis = create_hypothesis(
                hypothesis_id=f"h-{account.id}", account=account, statement=statement, evidence=evidence
            )
            lines.extend(("", "Supported opportunity hypothesis:", hypothesis.cautious_statement, "", "Status:", "HYPOTHESIS_SUPPORTED"))
        else:
            lines.extend(("", "Status:", "NO_SUPPORTED_HYPOTHESIS"))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
