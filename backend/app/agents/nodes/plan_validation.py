"""Node 4: Plan Validation Safeguard Node."""

import logging
from typing import Set, Dict
from backend.app.schemas.enums import StepStatus
from backend.app.agents.state import AgriMindState
from backend.app.core.config import settings

logger = logging.getLogger("agrimind.node.plan_validation")


def plan_validation_node(state: AgriMindState) -> AgriMindState:
    """
    Validates the generated execution plan against system safeguards:
    1. Plan existence and non-emptiness.
    2. Maximum step count limit (safeguard against runaway plans).
    3. Cycle detection in dependency DAG.
    """
    logger.info("Executing Plan Validation Node")

    if not state.execution_plan or not state.execution_plan.steps:
        state.execution_errors.append("Plan Validation Error: Execution plan is empty.")
        return state

    steps = state.execution_plan.steps

    # 1. Check max steps safeguard
    if len(steps) > settings.MAX_PLAN_STEPS:
        state.execution_errors.append(
            f"Plan Validation Error: Step count ({len(steps)}) exceeds system limit ({settings.MAX_PLAN_STEPS})."
        )
        return state

    # 2. Cycle detection (Topological sort verification)
    step_ids = {s.step_id for s in steps}
    adj: Dict[str, list[str]] = {s.step_id: [] for s in steps}

    for s in steps:
        for dep in s.dependencies:
            if dep not in step_ids:
                state.execution_errors.append(
                    f"Plan Validation Error: Step '{s.step_id}' depends on non-existent step '{dep}'."
                )
                return state
            adj[dep].append(s.step_id)

    # Standard cycle detection using DFS coloring
    visited: Dict[str, int] = {s.step_id: 0 for s in steps}  # 0: unvisited, 1: visiting, 2: visited

    def has_cycle(u: str) -> bool:
        visited[u] = 1
        for v in adj[u]:
            if visited[v] == 1:
                return True
            if visited[v] == 0 and has_cycle(v):
                return True
        visited[u] = 2
        return False

    for s in steps:
        if visited[s.step_id] == 0:
            if has_cycle(s.step_id):
                state.execution_errors.append("Plan Validation Error: Cyclic dependency detected in execution DAG.")
                return state

    state.execution_plan.is_validated = True
    logger.info(f"Plan validation successful: DAG verified with {len(steps)} steps.")
    return state
