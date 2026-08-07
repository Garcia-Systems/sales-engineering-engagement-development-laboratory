"""Chapter 5: deterministic signal analysis of the Chapter 4 research brief."""

from dataclasses import dataclass
from datetime import date

from engagement_dev.domain import (
    AccountEvidence,
    EvidenceCategory,
    ObservedSignal,
    PublicSourceType,
    ResearchDimension,
    SignalCluster,
    SignalInterpretation,
    SignalPolarity,
    SignalType,
    SourceReliability,
)
from engagement_dev.scenarios.chapter_four import load_chapter_four
from engagement_dev.services import (
    SignalEvaluation,
    SignalEvaluationStatus,
    SignalEvaluator,
    classify_freshness,
)


@dataclass(frozen=True)
class ChapterFiveAnalysis:
    brief: object
    candidates: tuple[ObservedSignal, ...]
    evaluations: tuple[SignalEvaluation, ...]
    cluster: SignalCluster
    duplicate_report_count: int
    underlying_expansion_events: int

    @property
    def supported(self) -> tuple[SignalEvaluation, ...]:
        return tuple(
            item
            for item in self.evaluations
            if item.status is SignalEvaluationStatus.SIGNAL_SUPPORTED
        )

    @property
    def rejected(self) -> tuple[SignalEvaluation, ...]:
        return tuple(
            item
            for item in self.evaluations
            if item.status is not SignalEvaluationStatus.SIGNAL_SUPPORTED
        )


def analyze_chapter_five() -> ChapterFiveAnalysis:
    brief = load_chapter_four()
    by_id = {item.id: item for item in brief.evidence}

    def report(
        identifier: str, description: str, source: str, observed_on: date
    ) -> AccountEvidence:
        return AccountEvidence(
            identifier,
            brief.account.id,
            description,
            EvidenceCategory.PUBLIC_FACT,
            source,
            ("SYSTEM_INTEGRATION",),
            False,
            PublicSourceType.PUBLIC_NEWS_ARTICLE,
            SourceReliability.SECONDARY_PUBLIC_SOURCE,
            observed_on,
            ResearchDimension.CHANGE,
        )

    expansion_reports = (
        report(
            "r5-news-1",
            "Fourth property announced.",
            "Fictional Coastal Ledger",
            date(2026, 7, 1),
        ),
        report(
            "r5-news-2",
            "Fourth property announced.",
            "Fictional Hospitality Weekly",
            date(2026, 7, 2),
        ),
        report(
            "r5-news-3",
            "Fourth property announced.",
            "Fictional Regional News",
            date(2026, 7, 3),
        ),
    )
    generic = AccountEvidence(
        "r8",
        brief.account.id,
        "“We are committed to innovation.”",
        EvidenceCategory.PUBLIC_FACT,
        "Blue Heron Resort marketing page",
        (),
        False,
        PublicSourceType.COMPANY_WEBSITE,
        SourceReliability.PRIMARY_PUBLIC_SOURCE,
        date(2026, 7, 22),
        ResearchDimension.ORGANIZATION,
    )

    def signal(
        identifier,
        evidence,
        signal_type,
        meaning,
        problems,
        questions,
        event,
        polarity=SignalPolarity.POSITIVE,
    ):
        return ObservedSignal(
            identifier,
            brief.account.id,
            evidence[0].description,
            EvidenceCategory.PUBLIC_FACT,
            evidence[0].source,
            signal_type,
            evidence,
            evidence[0].observed_on,
            classify_freshness(evidence[0].observed_on, brief.research_date),
            event,
            SignalInterpretation(evidence[0].description, meaning, problems, questions),
            polarity,
        )

    candidates = (
        signal(
            "signal-expansion",
            (by_id["r5"],) + expansion_reports,
            SignalType.EXPANSION,
            "Expansion may increase operational coordination requirements.",
            ("SYSTEM_INTEGRATION", "PROCESS_VISIBILITY", "DATA_SYNCHRONIZATION"),
            (
                "How are operational systems being extended to the new property?",
                "Are workflows standardized across properties?",
                "What processes change when the fourth property opens?",
            ),
            "event-fourth-property",
        ),
        signal(
            "signal-hiring",
            (by_id["r4"],),
            SignalType.HIRING,
            "The organization may be investing in coordination among operational systems.",
            ("SYSTEM_INTEGRATION", "PROCESS_VISIBILITY", "MANUAL_WORKFLOW"),
            (
                "Is the Operations Systems Coordinator role new?",
                "What initiative prompted the hiring?",
                "Which systems fall under the role?",
            ),
            "event-operations-hire",
        ),
        signal(
            "signal-platform",
            (by_id["r7"],),
            SignalType.TECHNOLOGY_CHANGE,
            "The completed platform deployment may reduce or change earlier synchronization concerns.",
            ("SYSTEM_INTEGRATION", "PROCESS_VISIBILITY"),
            (
                "Why was the centralized reservation platform introduced?",
                "What workflows remain outside it?",
                "How do reservations move between the central platform and other operational workflows?",
            ),
            "event-reservation-platform",
            SignalPolarity.NEGATIVE,
        ),
        signal(
            "signal-manual-history",
            (by_id["r6"],),
            SignalType.PROCESS_CHANGE,
            "Manual coordination was historically reported, but may no longer describe current operations.",
            ("MANUAL_WORKFLOW",),
            ("Which, if any, manual coordination steps remain?",),
            "event-manual-booking",
        ),
        signal(
            "signal-generic",
            (generic,),
            SignalType.ORGANIZATIONAL_CHANGE,
            "Generic language alone has no specific operational meaning.",
            (),
            ("What specific initiative, if any, does this statement refer to?",),
            "event-marketing-copy",
        ),
    )
    evaluator = SignalEvaluator()
    evaluations = tuple(
        evaluator.evaluate(item, brief.relevant_problem_class_ids)
        for item in candidates
    )
    cluster = evaluator.build_cluster(
        identifier="cluster-operational-scaling",
        account_id=brief.account.id,
        theme="Operational Scaling and Systems Coordination",
        evaluations=evaluations[:3],
        interpretation="Independent current changes justify deeper investigation; they do not establish a problem.",
        questions=(
            "How are responsibilities and workflows changing as the fourth property opens?",
            "Which coordination needs are addressed by the platform and systems roles?",
            "What evidence would show that the issue is absent, different, or already solved?",
        ),
    )
    return ChapterFiveAnalysis(
        brief, candidates, evaluations, cluster, len(expansion_reports), 1
    )


def chapter_five_report() -> str:
    analysis = analyze_chapter_five()
    lines = [
        "CHAPTER 5 — FINDING AND INTERPRETING SIGNALS",
        "",
        "ACCOUNT",
        analysis.brief.account.name,
    ]
    for number, evaluation in enumerate(analysis.supported, 1):
        signal = evaluation.signal
        lines += [
            "",
            "---",
            "",
            f"SIGNAL {number}",
            "",
            "Type:",
            signal.signal_type.value,
            "",
            "Observation:",
            signal.description,
            "",
            "Evidence:",
        ]
        lines += [f"- {item.source} ({item.id})" for item in signal.supporting_evidence]
        lines += [
            "",
            "Interpretation:",
            signal.interpretation.possible_meaning,
            "",
            "Relevant problem classes:",
        ]
        lines += [
            f"- {item}" for item in signal.interpretation.relevant_problem_class_ids
        ]
        lines += ["", "Strength:", evaluation.strength.value, "", "Unknowns:"]
        lines += [f"- {item}" for item in signal.interpretation.unresolved_questions]
        if evaluation.weakened_interpretation:
            lines += ["", "NEGATIVE SIGNAL EFFECT", evaluation.weakened_interpretation]
    lines += [
        "",
        "---",
        "",
        "SIGNAL CLUSTER",
        "",
        "Theme:",
        analysis.cluster.theme,
        "",
        "Signals:",
    ]
    lines += [
        f"- {item.signal_type.value}: {item.description}"
        for item in analysis.cluster.signals
    ]
    lines += [
        "",
        "Evaluation:",
        "STRONG BASIS FOR FURTHER INVESTIGATION",
        "",
        "Cluster questions:",
    ]
    lines += [f"- {item}" for item in analysis.cluster.unresolved_questions]
    lines += [
        "",
        "IMPORTANT:",
        "Strong basis for investigation does not mean a customer problem has been established.",
    ]
    for evaluation in analysis.rejected:
        lines += [
            "",
            "---",
            "",
            "REJECTED OBSERVATION",
            "",
            evaluation.signal.description,
            "",
            "Result:",
            evaluation.status.value,
            "",
            "Reason:",
            evaluation.reasons[0],
        ]
    lines += [
        "",
        "---",
        "",
        "DUPLICATE REPORTING",
        "",
        f"{analysis.duplicate_report_count} articles repeat the same expansion announcement.",
        "",
        "Underlying events:",
        str(analysis.underlying_expansion_events),
        "",
        "Not:",
        f"{analysis.duplicate_report_count + 1} independent signals.",
        "",
        "FALSIFIABILITY",
        "Questions must be able to reveal a problem, no problem, a different problem, or an issue already solved.",
        "",
        "SIGNAL ≠ PROBLEM",
        "STRONG SIGNAL ≠ QUALIFIED OPPORTUNITY",
        "",
        "SIGNAL ANALYSIS STATUS",
        "",
        f"Supported signals: {len(analysis.supported)}",
        f"Rejected observations: {len(analysis.rejected)}",
        "Signal clusters: 1",
        "",
        "Opportunity hypotheses validated: 0",
        "",
        "No customer problem has been validated.",
        "No engagement candidate has been created.",
        "",
        "NEXT STEP",
        "",
        "Use supported signals to construct explicit, falsifiable opportunity hypotheses.",
    ]
    return "\n".join(lines) + "\n"
