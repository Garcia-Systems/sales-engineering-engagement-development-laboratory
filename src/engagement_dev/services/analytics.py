"""Deterministic descriptive analytics over the existing lifecycle ledger."""

from collections import Counter
from engagement_dev.domain import (
    ActivityEvent,
    ActivityType,
    AnalyticsWarning,
    BottleneckFinding,
    BottleneckKind,
    ClosureLevel,
    ClosureReason,
    EngagementDevelopmentHistory,
    HypothesisStatus,
    ImprovementHypothesis,
    PipelineState,
    ProcessMetrics,
    StageTransitionSummary,
    StateDurationSummary,
)


EVIDENCE_ACTIVITY_TYPES = frozenset(
    {ActivityType.EVIDENCE_REVIEWED, ActivityType.CONVERSATION_HELD}
)


def activity_produced_evidence(event: ActivityEvent) -> bool:
    """Classify the recorded event, not effort or usefulness, with an explicit rule."""
    if event.activity_type not in EVIDENCE_ACTIVITY_TYPES:
        return False
    description = event.description.casefold()
    return not any(
        word in description for word in ("duplicate", "without", "no new evidence")
    )


def _authoritative_histories(history: EngagementDevelopmentHistory):
    closures = {record.account.id: record.state_history for record in history.closures}
    return tuple(
        closures.get(item.account.id, item.state_history)
        for item in history.pipeline_items
    )


class ProcessAnalyzer:
    """Projects descriptions from history; never mutates or predicts from it."""

    def metrics(self, history: EngagementDevelopmentHistory) -> ProcessMetrics:
        items = history.pipeline_items
        transitions = Counter()
        durations: dict[PipelineState, list[int]] = {}
        for events in _authoritative_histories(history):
            for left, right in zip(events, events[1:]):
                transitions[(left.state, right.state)] += 1
                durations.setdefault(left.state, []).append(
                    (right.occurred_on - left.occurred_on).days
                )

        closure_counts = Counter(record.observed_reason for record in history.closures)
        # UNKNOWN remains visible even when its observed count is zero.
        closure_counts.setdefault(ClosureReason.UNKNOWN, 0)
        market: dict[str, Counter[str]] = {}
        for item in items:
            values = market.setdefault(item.account.market_id, Counter())
            values["accounts_researched"] += item.research_brief is not None or bool(
                item.state_history
            )
            values["supported_hypotheses"] += bool(
                item.hypothesis
                and item.hypothesis.status
                in {
                    HypothesisStatus.SUPPORTED_FOR_VALIDATION,
                    HypothesisStatus.VALIDATED,
                }
            )
            values["engagement_candidates"] += item.engagement_candidate is not None

        activities = tuple(event for item in items for event in item.activities)
        counts = Counter(
            accounts_considered=history.accounts_considered or len(items),
            accounts_selected_for_research=len(items),
            research_briefs_completed=sum(
                item.research_brief is not None for item in items
            ),
            accounts_with_insufficient_evidence=sum(
                item.hypothesis is None and item.engagement_candidate is None
                for item in items
            ),
            accounts_closed_during_research=sum(
                record.level is ClosureLevel.RESEARCH_CLOSURE
                for record in history.closures
            ),
            supported_signals_identified=sum(
                signal.is_direct_evidence for item in items for signal in item.signals
            ),
            hypotheses_created=sum(item.hypothesis is not None for item in items),
            hypotheses_supported=sum(
                bool(
                    item.hypothesis
                    and item.hypothesis.status
                    in {
                        HypothesisStatus.SUPPORTED_FOR_VALIDATION,
                        HypothesisStatus.VALIDATED,
                    }
                )
                for item in items
            ),
            stakeholder_maps_completed=sum(
                item.stakeholder_map is not None for item in items
            ),
            outreach_messages_prepared=sum(item.outreach is not None for item in items),
            simulated_outreach_attempts=sum(
                bool(
                    item.outreach
                    and item.outreach.status.value
                    in {"SENT_SIMULATED", "NO_RESPONSE", "REPLIED", "DECLINED"}
                )
                for item in items
            ),
            responses_observed=sum(
                bool(
                    item.outreach
                    and item.outreach.status.value in {"REPLIED", "DECLINED"}
                )
                for item in items
            ),
            stakeholder_conversations=sum(
                item.conversation is not None for item in items
            ),
            qualification_assessments=sum(
                item.qualification is not None for item in items
            ),
            engagement_candidates=sum(
                item.engagement_candidate is not None for item in items
            ),
            handoffs_created=sum(
                bool(
                    item.engagement_candidate
                    and item.engagement_candidate.handoff_status == "READY"
                )
                for item in items
            ),
            reopen_conditions=sum(
                record.reopen_condition is not None for record in history.closures
            ),
        )
        sample = counts["accounts_considered"]
        warnings = (AnalyticsWarning.DESCRIPTIVE_ONLY,)
        if sample < 30:
            warnings += (AnalyticsWarning.INSUFFICIENT_SAMPLE,)
        return ProcessMetrics(
            tuple(sorted(counts.items())),
            tuple(
                StageTransitionSummary(a, b, n)
                for (a, b), n in sorted(
                    transitions.items(),
                    key=lambda value: (value[0][0].value, value[0][1].value),
                )
            ),
            tuple(
                StateDurationSummary(state, len(values), sum(values) / len(values))
                for state, values in sorted(
                    durations.items(), key=lambda value: value[0].value
                )
            ),
            tuple(sorted(closure_counts.items(), key=lambda value: value[0].value)),
            tuple(
                (name, tuple(sorted(values.items())))
                for name, values in sorted(market.items())
            ),
            len(activities),
            sum(activity_produced_evidence(event) for event in activities),
            warnings,
        )

    def bottleneck(self, metrics: ProcessMetrics) -> BottleneckFinding:
        attempts = metrics.count("simulated_outreach_attempts")
        responses = metrics.count("responses_observed")
        if attempts >= 1 and responses * 2 < attempts:
            kind = BottleneckKind.OUTREACH_RESPONSE_BOTTLENECK
            evidence = (
                f"{metrics.count('hypotheses_supported')} supported hypotheses were observed.",
                f"{attempts} simulated outreach attempts occurred.",
                f"{responses} responses were observed.",
            )
            interpretation = (
                "The outreach-to-response transition deserves investigation."
            )
        elif metrics.count("accounts_considered") < 5:
            kind = BottleneckKind.INSUFFICIENT_SAMPLE
            evidence = (
                f"Only {metrics.count('accounts_considered')} accounts were observed.",
            )
            interpretation = (
                "Collect more lifecycle evidence before treating a pattern as stable."
            )
        else:
            kind = BottleneckKind.NO_CLEAR_BOTTLENECK
            evidence = (
                "No stage has enough disproportionate stopping evidence for a clear finding.",
            )
            interpretation = "Continue observing the process."
        return BottleneckFinding(kind, evidence, interpretation)

    def improvement_hypothesis(
        self, finding: BottleneckFinding
    ) -> ImprovementHypothesis:
        # Debug breakpoint: above is DATA; this falsifiable proposition is INTERPRETATION.
        return ImprovementHypothesis(
            "Signal-specific outreach may produce more substantive responses than generic capability-led outreach.",
            finding.evidence,
            "A controlled next cycle shows no increase in substantive responses under the changed opening.",
        )
