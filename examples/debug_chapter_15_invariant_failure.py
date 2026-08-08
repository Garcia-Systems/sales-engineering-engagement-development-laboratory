"""Intentionally invalid isolated fixture for inspecting invariant rejection."""

from dataclasses import replace

from engagement_dev.domain import EngagementCandidate
from engagement_dev.simulation import (
    EngagementDevelopmentSimulator, SimulationConfig, SimulationInvariantChecker,
)


valid = EngagementDevelopmentSimulator(SimulationConfig()).run()
item = valid.pipeline_items[1]
invalid_candidate = EngagementCandidate("invalid", item.account.id, "unsupported", "missing")
invalid_item = replace(item, engagement_candidate=invalid_candidate)
invalid = replace(valid, pipeline_items=(invalid_item,) + valid.pipeline_items[1:], invariants=())
SimulationInvariantChecker().check(invalid)  # expected SimulationInvariantError
