"""Focused Chapter 6 debugger entry point."""

from engagement_dev.scenarios import analyze_chapter_six


analysis = analyze_chapter_six()
signal_cluster = analysis.chapter_five.cluster
candidate_a = analysis.candidates[0]
candidate_b = analysis.candidates[1]
evidence_chain = candidate_a.hypothesis.evidence_chain
candidate_statement = candidate_a.hypothesis.cautious_statement
problem_class = candidate_a.hypothesis.relevant_problem_class_ids
assumptions = candidate_a.hypothesis.assumptions
unknowns = candidate_a.hypothesis.unknowns
falsification_conditions = candidate_a.hypothesis.falsification_conditions
evaluator_result = candidate_a.evaluation
solution_first_result = candidate_b.evaluation

print(evaluator_result.outcome.value)
print(solution_first_result.outcome.value)
