"""Router and adaptive execution engine package exports."""

from backend.app.routing.scoring import is_hard_eligible, score_candidate
from backend.app.routing.router import ModelRouter, default_router
from backend.app.routing.engine import RoutedExecutionEngine, default_engine

__all__ = [
    "is_hard_eligible",
    "score_candidate",
    "ModelRouter",
    "default_router",
    "RoutedExecutionEngine",
    "default_engine",
]
