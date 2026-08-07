"""Focused Chapter 12 debugger: stop in derive_pipeline_state and inspect evidence."""
from engagement_dev.scenarios.chapter_twelve import analyze_chapter_twelve
from engagement_dev.services import derive_pipeline_state, next_justified_action

analysis = analyze_chapter_twelve()
for pipeline_item in analysis.items:
    account = pipeline_item.account
    underlying_evidence = pipeline_item
    derived_state = derive_pipeline_state(pipeline_item)  # Set a breakpoint here or inside the policy.
    state_history = pipeline_item.state_history
    next_action = next_justified_action(pipeline_item)
capacity_allocation = analysis.allocation
print(account.name, derived_state.value, next_action.description, len(state_history), len(capacity_allocation.selected))
