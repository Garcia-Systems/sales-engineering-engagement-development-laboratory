"""Focused Chapter 4 debugger: inspect the brief and readiness result."""

from engagement_dev.scenarios import load_chapter_four
from engagement_dev.services import AccountResearchEvaluator, classify_freshness

brief = load_chapter_four()
research_evidence = brief.evidence
source_type = research_evidence[0].source_type
source_reliability = research_evidence[0].source_reliability
freshness = classify_freshness(research_evidence[0].observed_on, brief.research_date)
observation = research_evidence[0]
inference = brief.inferences[0]
unknown = brief.unknowns[0]
evidence_conflicts = brief.conflicts
research_readiness_result = AccountResearchEvaluator().evaluate(brief)

print(research_readiness_result.status)
