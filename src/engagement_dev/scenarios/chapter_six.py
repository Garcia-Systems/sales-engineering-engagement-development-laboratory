"""Chapter 6: form provisional, falsifiable explanations from Chapter 5 signals."""

from dataclasses import dataclass

from engagement_dev.domain import Assumption, HypothesisUnknown, UnknownCategory
from engagement_dev.scenarios.chapter_five import analyze_chapter_five
from engagement_dev.services import (
    HypothesisEvaluationOutcome,
    OpportunityHypothesisBuilder,
    OpportunityHypothesisEvaluation,
    OpportunityHypothesisEvaluator,
)


@dataclass(frozen=True)
class EvaluatedCandidate:
    label: str
    hypothesis: object
    evaluation: OpportunityHypothesisEvaluation


@dataclass(frozen=True)
class ChapterSixAnalysis:
    chapter_five: object
    candidates: tuple[EvaluatedCandidate, ...]

    @property
    def supported(self):
        return tuple(item for item in self.candidates if item.evaluation.outcome is HypothesisEvaluationOutcome.SUPPORTED_FOR_VALIDATION)

    @property
    def rejected(self):
        return tuple(item for item in self.candidates if item not in self.supported)


def analyze_chapter_six() -> ChapterSixAnalysis:
    previous = analyze_chapter_five()
    account, cluster = previous.brief.account, previous.cluster
    assumptions = (
        Assumption("a1", "Multiple operational systems participate."),
        Assumption("a2", "Expansion changes workflow volume or complexity."),
        Assumption("a3", "Coordination effort may be material."),
    )
    unknowns = (
        HypothesisUnknown(UnknownCategory.CURRENT_PROCESS, "How are workflows coordinated today?"),
        HypothesisUnknown(UnknownCategory.PROBLEM_EXISTENCE, "Is there any material coordination difficulty?"),
        HypothesisUnknown(UnknownCategory.BUSINESS_IMPACT, "What business impact, if any, occurs?"),
        HypothesisUnknown(UnknownCategory.TECHNICAL_ENVIRONMENT, "What initiatives or systems already address this?"),
        HypothesisUnknown(UnknownCategory.STAKEHOLDER, "Who owns the relevant workflows?"),
        HypothesisUnknown(UnknownCategory.URGENCY, "Is timing material?"),
        HypothesisUnknown(UnknownCategory.BUDGET, "Has any budget been established?"),
        HypothesisUnknown(UnknownCategory.EXTERNAL_HELP_ACCEPTANCE, "Is external assistance of interest?"),
    )
    falsification = (
        "Unified workflows already handle expansion cleanly.",
        "Hiring is simple replacement hiring.",
        "Stakeholders report no meaningful coordination issue.",
        "The relevant initiative has already been completed.",
    )
    questions = (
        "How are operational workflows changing as the fourth property is added?",
        "Which processes span multiple properties?",
        "How are reservations, events, and property operations coordinated today?",
        "What prompted the Operations Systems Coordinator role?",
        "Which parts of the current process require the most coordination?",
        "What has already been changed or improved?",
        "Are there areas where the current process is working particularly well?",
    )
    specs = (
        ("A", "Expansion may be increasing coordination requirements across reservation, event, and property operations.", cluster.signals, ("SYSTEM_INTEGRATION", "PROCESS_VISIBILITY"), "Expansion, hiring, and a platform change offer a related but not conclusive explanation.", "operational-scaling"),
        ("B", "Blue Heron Resort needs a custom API integration platform.", cluster.signals, ("SYSTEM_INTEGRATION",), "A proposed implementation is being mistaken for an observed problem.", ""),
        ("C", "Blue Heron Resort's systems are broken.", cluster.signals, ("SYSTEM_INTEGRATION",), "The evidence observes changes, not system failure.", ""),
        ("D", "The Operations Systems Coordinator posting may represent replacement hiring rather than a new initiative.", (cluster.signals[1],), ("PROCESS_VISIBILITY",), "The hiring signal permits an ordinary competing explanation.", "operational-scaling"),
    )
    builder, evaluator = OpportunityHypothesisBuilder(), OpportunityHypothesisEvaluator()
    candidates = []
    for label, statement, signals, problems, reasoning, group in specs:
        draft = builder.build(
            identifier=f"hypothesis-{label.lower()}", account=account, statement=statement,
            cluster=cluster, supporting_signals=signals, relevant_problem_class_ids=problems,
            reasoning=reasoning, assumptions=assumptions, unknowns=unknowns,
            falsification_conditions=falsification, validation_questions=questions,
            competing_group_id=group,
        )
        hypothesis, evaluation = evaluator.evaluate(
            draft, signals=cluster.signals,
            supported_problem_class_ids=previous.brief.relevant_problem_class_ids,
        )
        candidates.append(EvaluatedCandidate(label, hypothesis, evaluation))
    return ChapterSixAnalysis(previous, tuple(candidates))


def chapter_six_report() -> str:
    analysis = analyze_chapter_six()
    account = analysis.chapter_five.brief.account
    lines = ["CHAPTER 6 — FORMING AN OPPORTUNITY HYPOTHESIS", "", "CANDIDATE EVALUATION"]
    for item in analysis.candidates:
        lines += ["", f"CANDIDATE {item.label}", item.hypothesis.cautious_statement, "", "RESULT", item.evaluation.outcome.value, "", "WHY", *[f"- {finding}" for finding in item.evaluation.findings]]
    primary = analysis.candidates[0].hypothesis
    lines += ["", "---", "", "OPPORTUNITY HYPOTHESIS BRIEF", "", "ACCOUNT", account.name, "", "HYPOTHESIS", primary.cautious_statement, "", "STATUS", primary.status.value, "", "EVIDENCE CHAIN"]
    evidence = {item.id: item for signal in analysis.chapter_five.cluster.signals for item in signal.supporting_evidence}
    signal = {item.id: item for item in analysis.chapter_five.cluster.signals}
    for link in primary.evidence_chain:
        lines += [f"- Evidence: {evidence[link.evidence_id].description} ({link.evidence_id})", f"  ↓ Signal: {signal[link.signal_id].signal_type.value} ({link.signal_id})"]
    lines += [f"  ↓ Signal Cluster: {analysis.chapter_five.cluster.theme}", f"  ↓ Opportunity Hypothesis: {primary.cautious_statement}", "", "RELEVANT PROBLEM CLASSES", *[f"- {item}" for item in primary.relevant_problem_class_ids], "", "ASSUMPTIONS"]
    lines += [f"- [{item.status.value}] {item.statement}" for item in primary.assumptions]
    lines += ["", "UNKNOWNS", *[f"- {item.category.value}: {item.question}" for item in primary.unknowns], "", "FALSIFICATION CONDITIONS", *[f"- {item}" for item in primary.falsification_conditions], "", "VALIDATION QUESTIONS", *[f"- {item}" for item in primary.validation_questions], "", "IMPORTANT", "This is a hypothesis to investigate.", "It is not a confirmed customer problem.", "", "COMPETING EXPLANATION", analysis.candidates[3].hypothesis.cautious_statement, "", "OPPORTUNITY HYPOTHESES", f"Supported for validation: {len(analysis.supported)}", f"Rejected: {len(analysis.rejected)}", "Competing explanations: 1", "", "CONFIRMED CUSTOMER PROBLEMS", "0", "", "QUALIFIED ENGAGEMENTS", "0", "", "NEXT STEP", "Identify the people and roles capable of providing evidence that confirms, refines, or refutes the hypothesis."]
    return "\n".join(lines) + "\n"
