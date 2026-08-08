# Sales Engineering Engagement Development Laboratory

This deterministic executable textbook teaches the upstream work **before** a formal Sales Engineering Laboratory engagement: finding and justifying a legitimate opportunity without manufacturing one. It uses educational simulations, not external APIs, fake CRM integrations, autonomous outreach, or probabilistic scores presented as truth.

```mermaid
flowchart TD
  Market --> Account --> Signals[Observed Signals] --> Hypothesis[Opportunity Hypothesis]
  Hypothesis --> StakeholderMap[Stakeholder Map] --> ContactStrategy[Contact Strategy] --> Conversation --> Qualification --> Engagement
  ContactStrategy --> FollowUp[Respectful Follow-Up] --> ContactStrategy
```

The reasoning chain is **Market → Account → Signal → Opportunity Hypothesis → Stakeholder Map → Contact Strategy → Conversation → Qualification → Engagement**. Every transition needs appropriate evidence. In particular:

- Activity ≠ Progress
- Contact ≠ Opportunity
- Conversation ≠ Qualification
- Qualification ≠ Closed sale
- Analysis ≠ Customer approval

“No qualified opportunity exists yet” is a successful analytical conclusion, not a failure. Inferences remain labeled as inferences and cannot alone support a hypothesis. The examples are fictional and deterministic.

## Run it

Python 3.13 is required.

```bash
python -m pip install -e '.[dev]'
engagement-dev chapter-0
engagement-dev chapter-2
engagement-dev chapter-3
engagement-dev chapter-4
engagement-dev chapter-5
engagement-dev chapter-6
engagement-dev chapter-7
engagement-dev chapter-8
engagement-dev chapter-9
engagement-dev chapter-10
engagement-dev chapter-11
engagement-dev chapter-12
engagement-dev chapter-13
engagement-dev chapter-14
engagement-dev chapter-15 --scenario productive
engagement-dev chapter-15 --scenario zero-engagement
engagement-dev chapter-15 --scenario capacity-constrained
# or
python -m engagement_dev.cli chapter-0
pytest
```

The immutable domain records live in `engagement_dev.domain`; creation policies live in `engagement_dev.services`. This separation makes it easy to inspect both a conclusion and the evidence identifiers behind it. The VS Code **Chapter 0** launch configuration supports stepping through the scenario.

## Chapter roadmap

- [Chapter 0 — From No Engagement to a Legitimate Opportunity](chapters/chapter_00_foundations.md) establishes the evidence-led lifecycle and its handoff boundary.
- [Chapter 1 — Define the Offer Before Looking for Prospects](chapters/chapter_01_define_the_offer.md) establishes **Capability → Problem Class → Evidence of Fit → Investigation Boundary** before market or account selection.
- [Chapter 2 — Choosing a Market](chapters/chapter_02_choosing_a_market.md) implements **Supported Offer → Market Evidence → Market Hypothesis → Investigation Priority** as an allocation-of-attention decision.

Chapter 3 — [Building an Account List](chapters/chapter_03_building_an_account_list.md) implements **Selected Market → Account Evidence → Research Rationale → Account Research Queue** while keeping the queue distinct from an opportunity pipeline.

[Chapter 4 — Researching an Account](chapters/chapter_04_researching_an_account.md) implements **Account Research Queue → Public Evidence → Account Research Brief → Research Readiness** while preserving facts, observations, inferences, unknowns, provenance, freshness, and conflicts.

[Chapter 5 — Finding and Interpreting Signals](chapters/chapter_05_finding_and_interpreting_signals.md) implements **Account Research Brief → Candidate Observations → Signal Evaluation → Signal Clusters → Investigation Questions**. It preserves **Signal ≠ Problem**, detects duplicate reporting, and creates no opportunity hypothesis.

[Chapter 6 — Forming an Opportunity Hypothesis](chapters/chapter_06_forming_an_opportunity_hypothesis.md) implements **Signal Cluster → Candidate Explanations → Opportunity Hypothesis → Validation Questions**. It preserves assumptions, unknowns, falsification paths, and competing explanations while enforcing **Possible Problem ≠ Proposed Solution**.

[Chapter 7 — Mapping the Buying Organization](chapters/chapter_07_mapping_the_buying_organization.md) implements **Opportunity Hypothesis → Validation Questions → Knowledge Needed → Stakeholder Map → Evidence-Oriented Contact Priority** while preserving unknown authority and sending no outreach.

[Chapter 8 — Designing Evidence-Based Outreach](chapters/chapter_08_designing_evidence_based_outreach.md) implements **Public Evidence + Opportunity Hypothesis + Stakeholder Relevance + Supported Credibility → Outreach Draft → Evidence Validation → READY** while sending no external communication.

[Chapter 9 — Running the First Conversation](chapters/chapter_09_running_the_first_conversation.md) implements **Opportunity Hypothesis → Neutral Validation Questions → Simulated Stakeholder Conversation → Stakeholder Evidence → Hypothesis Update**. It preserves statement provenance, supports refinement and refutation, selects no solution, and creates no qualification.

[Chapter 10 — Qualifying the Opportunity](chapters/chapter_10_qualifying_the_opportunity.md) implements **Customer-Grounded Evidence → Explicit Qualification Dimensions → Deterministic Threshold → Engagement Candidate → Evidence-Backed Handoff**. It is the first chapter permitted to create an `EngagementCandidate`, and does so only when the conservative threshold passes. Budget may remain explicitly unknown; no solution, architecture, deal value, or close probability is assumed.

[Chapter 11 — Managing Follow-Up Without Chasing](chapters/chapter_11_managing_follow_up_without_chasing.md) implements **Prior Interaction + Legitimate Reason + Contextual Timing + Stopping Rule → Simulated Follow-Up or Respectful Stop**. It keeps no response neutral, respects requested timing and strict no-contact states, limits no-response sequences, and never changes qualification or creates an engagement candidate merely because follow-up occurred.

[Chapter 12 — Building and Managing the Engagement Pipeline](chapters/chapter_12_building_and_managing_the_engagement_pipeline.md) implements **Existing Lifecycle Evidence → Derived Pipeline State → Next Justified Action → Capacity Allocation → New Evidence**. It preserves state history and regression, separates activity from progress, protects silent accounts, enforces simple WIP limits, and excludes fake revenue forecasts and close probabilities.

[Chapter 13 — Learning From Rejection, Closure, and Lost Opportunities](chapters/chapter_13_learning_from_rejection_closure_and_lost_opportunities.md) implements **Outcome Evidence → Closure or Defer Decision → Observed Reason → Supported Learning → Reopen Trigger**. It preserves pipeline history, accepts `UNKNOWN`, separates closure levels, rejects unsupported narratives, and prevents account evidence from becoming a market generalization.

[Chapter 14 — Engagement Development Analytics and Continuous Improvement](chapters/chapter_14_engagement_development_analytics_and_continuous_improvement.md) implements **Lifecycle History → Descriptive Metrics → Observed Pattern → Improvement Hypothesis → Controlled Next-Cycle Experiment**. It derives from existing pipeline and closure ledgers, preserves unknowns, separates activity from evidence yield, and makes no causal, revenue, or close-probability claim.

[Chapter 15 — Engagement Development Simulator](chapters/chapter_15_engagement_development_simulator.md) is the Volume I capstone. It orchestrates the existing chapter subsystems across productive, zero-engagement, and capacity-constrained cycles; preserves a deterministic event and evidence ledger; validates cross-chapter invariants; reuses the Chapter 10 handoff; and derives improvement through Chapter 14 analytics.

Chapters 0–15 are implemented and **Volume I is complete**. Chapter 10 completes the first major qualification lifecycle; Chapter 11 adds evidence-driven follow-up branches; Chapter 12 composes multiple accounts into an evidence-state portfolio without creating a parallel source of truth. Chapter 13 appends evidence-backed closure, Chapter 14 derives conservative process analytics, and Chapter 15 orchestrates a complete evidence-led cycle without guaranteeing an engagement.

## Volume I — From No Engagement to Qualified Engagement

1. Chapter 0 — From No Engagement to a Legitimate Opportunity
2. Chapter 1 — Define the Offer Before Looking for Prospects
3. Chapter 2 — Choosing a Market
4. Chapter 3 — Building an Account List
5. Chapter 4 — Researching an Account
6. Chapter 5 — Finding and Interpreting Signals
7. Chapter 6 — Forming an Opportunity Hypothesis
8. Chapter 7 — Mapping the Buying Organization
9. Chapter 8 — Designing Evidence-Based Outreach
10. Chapter 9 — Running the First Conversation
11. Chapter 10 — Qualifying the Opportunity
12. Chapter 11 — Managing Follow-Up Without Chasing
13. Chapter 12 — Building and Managing the Engagement Pipeline
14. Chapter 13 — Learning From Rejection, Closure, and Lost Opportunities
15. Chapter 14 — Engagement Development Analytics and Continuous Improvement
16. Chapter 15 — Engagement Development Simulator

Run Chapter 1 with `python -m engagement_dev.cli chapter-1`. Its fictional Northstar Systems Studio scenario evaluates bounded offers, vague language, and overclaims without treating proof of capability as proof of customer need.

## Laboratory boundary

Volume I ends with an evidence-backed `EngagementHandoff`. The separate Sales Engineering Laboratory begins with that handoff and teaches how to run the actual engagement. An `EngagementCandidate` is a handoff candidate—not a closed sale and not customer approval.

Start with [Chapter 0](chapters/chapter_00_foundations.md), continue sequentially through qualification and follow-up, manage the evidence-state portfolio in [Chapter 12](chapters/chapter_12_building_and_managing_the_engagement_pipeline.md), learn conservatively from closure in [Chapter 13](chapters/chapter_13_learning_from_rejection_closure_and_lost_opportunities.md), and use preserved history for process learning in [Chapter 14](chapters/chapter_14_engagement_development_analytics_and_continuous_improvement.md).

Run the completed capstone in [Chapter 15](chapters/chapter_15_engagement_development_simulator.md). A final QA/release pass is the recommended next step before expanding the laboratory or integrating more tightly with the downstream project.
