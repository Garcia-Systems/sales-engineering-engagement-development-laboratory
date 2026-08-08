# Chapter 0 — From No Engagement to a Legitimate Opportunity

![Evidence-led lifecycle from market context to a legitimate engagement opportunity](<../images/chapters/chapter_00_foundations.png>)

## Learning objectives

After this chapter, you can:

1. Distinguish prospecting activity from an actual sales engineering engagement.
2. Distinguish evidence from assumptions.
3. Explain why a company is not automatically an opportunity.
4. Explain why a contact is not automatically a buyer.
5. Explain why a conversation is not automatically qualification.
6. Recognize “no qualified opportunity” as a legitimate outcome.
7. Trace **Market → Account → Signal → Opportunity Hypothesis → Contact → Conversation → Qualification → Engagement**.

## The lifecycle

A **Market** supplies context; an **Account** is merely an organization in it. An **ObservedSignal** records a sourced claim. Only relevant evidence permits an **OpportunityHypothesis**: a cautious, testable reason to investigate. A **Contact** is a person, not automatically a buyer. A **Conversation** records what occurred, but its existence does not establish urgency, authority, budget, or technical fit. A **QualificationAssessment** makes an explicit condition and rationale inspectable. Only a passing, evidence-backed assessment permits an **EngagementCandidate**.

These are deliberately small immutable value objects. Their identifiers and references preserve the reasoning trail without pretending to be a CRM.

## Evidence before judgment

The laboratory labels evidence as `PUBLIC_FACT`, `OBSERVED_BEHAVIOR`, `STAKEHOLDER_STATEMENT`, or `INFERENCE`. The first three describe direct evidence with different provenance. `INFERENCE` is analyst judgment: useful for deciding what to investigate, but not equivalent to observation and never sufficient by itself to create a hypothesis.

Never invent pain, urgency, authority, budget, requirements, or interest. A public change may justify asking a question; it does not prove a need. Say, “Available evidence supports investigating whether this problem exists,” not, “This company needs our solution.”

## Interpreting the scenario

The fictional coastal market intentionally includes strong, ambiguous, irrelevant, and absent signals. The deterministic policy supports hypotheses only for accounts configured with a relevant question and direct evidence. Other accounts remain accounts. The correct result can be `NO_SUPPORTED_HYPOTHESIS`, and the correct end state can be **no qualified opportunity exists yet**.

Run `python -m engagement_dev.cli chapter-0`, then use the debugger to inspect how each supported hypothesis retains its evidence IDs. Notice the limits:

- Activity ≠ Progress
- Contact ≠ Opportunity
- Conversation ≠ Qualification
- Qualification ≠ Closed sale
- Analysis ≠ Customer approval

## Boundary

This laboratory ends when there is enough justified evidence to begin a structured sales engineering engagement. The downstream Sales Engineering Laboratory begins there. Chapter 0 stops earlier: it establishes the evidence discipline and traceability needed for every later step.
