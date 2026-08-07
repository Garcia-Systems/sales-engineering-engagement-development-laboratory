"""Focused Chapter 5 debugger exercise."""

from engagement_dev.scenarios.chapter_five import analyze_chapter_five
from engagement_dev.services import SignalEvaluator


analysis = analyze_chapter_five()
candidate_observation = analysis.candidates[0]
evidence = candidate_observation.supporting_evidence
signal_type = candidate_observation.signal_type
freshness = candidate_observation.freshness
underlying_event = candidate_observation.underlying_event_id
interpretation = candidate_observation.interpretation
relevant_problem_classes = interpretation.relevant_problem_class_ids
unresolved_questions = interpretation.unresolved_questions
evaluator_result = analysis.evaluations[
    0
]  # Breakpoint 1: inspect evidence and evaluation.
signal_strength = evaluator_result.strength

cluster = SignalEvaluator().build_cluster(  # Breakpoint 2: inspect related events and shared classes.
    identifier="debug-cluster",
    account_id=analysis.brief.account.id,
    theme=analysis.cluster.theme,
    evaluations=analysis.evaluations[:3],
    interpretation=analysis.cluster.cluster_interpretation,
    questions=analysis.cluster.unresolved_questions,
)
print(evaluator_result.status.value, signal_strength.value, cluster.strength.value)
