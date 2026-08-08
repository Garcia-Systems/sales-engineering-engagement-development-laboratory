"""Focused Chapter 14 debugger laboratory."""

from engagement_dev.scenarios.chapter_fourteen import analyze_chapter_fourteen
from engagement_dev.services.analytics import (
    ProcessAnalyzer,
    activity_produced_evidence,
)


analysis = analyze_chapter_fourteen()
lifecycle_history = analysis.history
stage_transition = analysis.metrics.transitions[0]
activity_event = next(
    event for item in lifecycle_history.pipeline_items for event in item.activities
)
evidence_producing_classification = activity_produced_evidence(activity_event)
bottleneck_evidence = analysis.retrospective.primary_bottleneck.evidence

# Set a breakpoint in ProcessAnalyzer.improvement_hypothesis: metrics above are
# DATA; the falsifiable proposition below begins INTERPRETATION.
improvement_hypothesis = ProcessAnalyzer().improvement_hypothesis(
    analysis.retrospective.primary_bottleneck
)
experiment = analysis.retrospective.improvement_plan.experiments[0]

print(stage_transition, evidence_producing_classification)
print(bottleneck_evidence)
print(improvement_hypothesis)
print(experiment)
