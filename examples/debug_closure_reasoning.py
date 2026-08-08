"""Focused Chapter 13 debugger: unsupported inference becomes UNKNOWN."""

from engagement_dev.scenarios.chapter_thirteen import analyze_chapter_thirteen


analysis = analyze_chapter_thirteen()
evaluation = analysis.unsupported_budget_evaluation  # breakpoint: inspect proposed and recorded reason
closure = analysis.closures[0]
debug_snapshot = {
    "proposed_closure_reason": evaluation.proposed_reason,
    "supporting_evidence": closure.supporting_evidence,
    "known_facts": evaluation.known_facts,
    "inferred_possibilities": evaluation.inferred_possibilities,
    "unknowns": evaluation.unknowns,
    "closure_level": evaluation.level,
    "supported_learning": closure.supported_lessons,
    "unsupported_generalization": closure.unsupported_lessons,
    "reopen_condition": closure.reopen_condition,
    "recorded_reason": evaluation.recorded_reason,
}
print(debug_snapshot)
