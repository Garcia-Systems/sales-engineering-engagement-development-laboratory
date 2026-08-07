"""Breakpoint-friendly Chapter 10 qualification laboratory."""
from engagement_dev.domain import QualificationDimensionName
from engagement_dev.scenarios.chapter_ten import analyze_chapter_ten

analysis = analyze_chapter_ten()
refined_hypothesis = analysis.assessment.refined_hypothesis
qualification_dimensions = analysis.assessment.dimensions
supporting_evidence = analysis.assessment.evidence_ids
unresolved_gaps = analysis.assessment.unresolved_gaps
threshold_evaluation = analysis.threshold_evaluation
engagement_candidate_creation_decision = analysis.candidate is not None
budget = analysis.assessment.dimension(QualificationDimensionName.BUDGET)
insufficient_impact = analysis.alternatives[2]

if __name__ == "__main__":
    print(analysis.assessment.outcome.value)
    print(f"Budget: {budget.state.value}; candidate created: {engagement_candidate_creation_decision}")
    print(f"Missing impact example: {insufficient_impact.outcome.value}")
