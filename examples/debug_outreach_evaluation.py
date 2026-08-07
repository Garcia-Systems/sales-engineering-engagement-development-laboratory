"""Focused Chapter 8 breakpoint laboratory."""

from engagement_dev.scenarios import analyze_chapter_eight


analysis = analyze_chapter_eight()
supported = analysis.candidates[0]
assumption_heavy = analysis.candidates[1]

# Break here: inspect each message's claims, evidence IDs, credibility proof, CTA, and result.
assert supported.evaluation.outcome.value == "SUPPORTED"
assert assumption_heavy.evaluation.outcome.value == "REJECTED_ASSUMPTIONS"
