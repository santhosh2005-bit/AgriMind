"""LangGraph workflow definition for the AgriMind agentic system."""

import logging
from typing import Literal, Callable, Any
from langgraph.graph import StateGraph, START, END

from backend.app.agents.state import AgriMindState
from backend.app.agents.nodes.input_validation import input_validation_node
from backend.app.agents.nodes.request_understanding import request_understanding_node
from backend.app.agents.nodes.planning import planning_node
from backend.app.agents.nodes.plan_validation import plan_validation_node
from backend.app.agents.nodes.step_executor import step_executor_node
from backend.app.agents.nodes.synthesizer import synthesizer_node
from backend.app.agents.nodes.verification import verification_node
from backend.app.agents.nodes.recovery import recovery_node
from backend.app.agents.nodes.final_response import final_response_node
from backend.app.schemas.enums import VerificationStatus

logger = logging.getLogger("agrimind.graph")


# State adapters for seamless LangGraph Pregel channel merging
def wrap_node(fn: Callable[[AgriMindState], AgriMindState]) -> Callable[[Any], dict]:
    """Wraps a typed node function to receive AgriMindState and return state.model_dump()."""
    def wrapped(state: Any) -> dict:
        state_obj = AgriMindState(**state) if isinstance(state, dict) else state
        out = fn(state_obj)
        return out.model_dump() if isinstance(out, AgriMindState) else out
    return wrapped


def wrap_decider(fn: Callable[[AgriMindState], str]) -> Callable[[Any], str]:
    """Wraps conditional routing edge decider functions."""
    def wrapped(state: Any) -> str:
        state_obj = AgriMindState(**state) if isinstance(state, dict) else state
        return fn(state_obj)
    return wrapped


# Conditional Edge Deciders
def route_after_input_validation(state: AgriMindState) -> Literal["node_request_understanding", "node_recovery"]:
    if state.execution_errors:
        return "node_recovery"
    return "node_request_understanding"


def route_after_plan_validation(state: AgriMindState) -> Literal["node_step_executor", "node_synthesizer", "node_recovery"]:
    if state.execution_errors:
        return "node_recovery"
    if state.get_next_step() is not None:
        return "node_step_executor"
    return "node_synthesizer"


def route_after_step_execution(state: AgriMindState) -> Literal["node_step_executor", "node_synthesizer", "node_recovery"]:
    if state.is_budget_exceeded() or state.loop_iteration_count >= state.max_loop_iterations:
        logger.warning("Execution loop or budget limit reached; terminating step loop.")
        return "node_synthesizer"

    if state.get_next_step() is not None:
        return "node_step_executor"

    return "node_synthesizer"


def route_after_verification(state: AgriMindState) -> Literal["node_recovery", "node_final_response"]:
    verif = state.verification_result
    if state.execution_errors or (verif and verif.overall_status in [VerificationStatus.FAILED, VerificationStatus.NEEDS_REVIEW]):
        return "node_recovery"
    return "node_final_response"


def build_agrimind_workflow():
    """Constructs the complete conditional LangGraph orchestration DAG."""
    builder = StateGraph(AgriMindState)

    # Add all 9 distinct nodes with LangGraph Pregel state wrapping
    builder.add_node("node_input_validation", wrap_node(input_validation_node))
    builder.add_node("node_request_understanding", wrap_node(request_understanding_node))
    builder.add_node("node_planning", wrap_node(planning_node))
    builder.add_node("node_plan_validation", wrap_node(plan_validation_node))
    builder.add_node("node_step_executor", wrap_node(step_executor_node))
    builder.add_node("node_synthesizer", wrap_node(synthesizer_node))
    builder.add_node("node_verification", wrap_node(verification_node))
    builder.add_node("node_recovery", wrap_node(recovery_node))
    builder.add_node("node_final_response", wrap_node(final_response_node))

    # Edges & Conditional Branching
    builder.add_edge(START, "node_input_validation")

    builder.add_conditional_edges(
        "node_input_validation",
        wrap_decider(route_after_input_validation),
        {
            "node_request_understanding": "node_request_understanding",
            "node_recovery": "node_recovery",
        },
    )

    builder.add_edge("node_request_understanding", "node_planning")
    builder.add_edge("node_planning", "node_plan_validation")

    builder.add_conditional_edges(
        "node_plan_validation",
        wrap_decider(route_after_plan_validation),
        {
            "node_step_executor": "node_step_executor",
            "node_synthesizer": "node_synthesizer",
            "node_recovery": "node_recovery",
        },
    )

    builder.add_conditional_edges(
        "node_step_executor",
        wrap_decider(route_after_step_execution),
        {
            "node_step_executor": "node_step_executor",
            "node_synthesizer": "node_synthesizer",
            "node_recovery": "node_recovery",
        },
    )

    builder.add_edge("node_synthesizer", "node_verification")

    builder.add_conditional_edges(
        "node_verification",
        wrap_decider(route_after_verification),
        {
            "node_recovery": "node_recovery",
            "node_final_response": "node_final_response",
        },
    )

    builder.add_edge("node_recovery", "node_final_response")
    builder.add_edge("node_final_response", END)

    return builder.compile()


# Compiled singleton workflow
agrimind_workflow = build_agrimind_workflow()
