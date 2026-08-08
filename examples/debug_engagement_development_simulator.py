"""Focused Chapter 15 breakpoint laboratory."""

from engagement_dev.simulation import EngagementDevelopmentSimulator, SimulationConfig


result = EngagementDevelopmentSimulator(SimulationConfig()).run()
for current_account in result.pipeline_items:
    phase = current_account.state_history[-1].state
    evidence_state = next(x for x in result.evidence_ledgers if x.account == current_account.account)
    pipeline_state = phase
    selected_service = "existing chapter subsystem"
    resulting_lifecycle_event = tuple(x for x in result.events if x.account_id == current_account.account.id)[-1]
    capacity_state = result.config
    final_outcome = evidence_state.final_outcome
    print(current_account.account.name, final_outcome.value)
