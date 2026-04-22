"""
Inference gateway adapter for runtime context.

This module provides the Phase 1 inference gateway as used by runtime_executor.
It wraps the canonical framework.inference_gateway implementation and provides
compatible functions (select_profile, load_runtime_profiles) for runtime modules.

All execution must use this single unified gateway. No other inference paths allowed.
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from framework.inference_gateway import InferenceGateway, GatewayRequest, GatewayResponse
from framework.model_profiles import get_profile, ModelProfile
import yaml


# Singleton instance of the canonical gateway
_gateway: Optional[InferenceGateway] = None


def _get_gateway() -> InferenceGateway:
    """Get or create the canonical inference gateway instance."""
    global _gateway
    if _gateway is None:
        _gateway = InferenceGateway()
    return _gateway


def load_runtime_profiles(path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load runtime profiles YAML authority for backward compatibility.

    This function loads the governance/runtime_profiles.v1.yaml file
    and returns its structure for inspection. The actual profile resolution
    uses framework.model_profiles.get_profile() which reads the same authority.

    Args:
        path: Optional override path to runtime_profiles.v1.yaml

    Returns:
        dict with profiles, selection_heuristics, metadata
    """
    if path is None:
        path = Path(__file__).parent.parent / "governance" / "runtime_profiles.v1.yaml"

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Runtime profiles not found at {path}")

    with open(path, "r") as f:
        data = yaml.safe_load(f)

    return data


def select_profile(
    goal: str,
    constraints: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Select a runtime profile (fast/balanced/hard) based on goal and constraints.

    Delegates to framework.model_profiles.resolve_profile_for_task_class() for actual
    profile resolution, ensuring all execution uses the canonical gateway selection.

    Args:
        goal: User-provided goal/task description
        constraints: Optional dict with explicit_escalation, require_fast, max_timeout_seconds

    Returns:
        dict with selected_profile, reasoning, and confidence
    """
    constraints = constraints or {}

    if constraints.get("explicit_escalation"):
        return {
            "selected_profile": "hard",
            "reason": "Explicit escalation requested",
            "factors": ["explicit_escalation"]
        }

    if constraints.get("require_fast"):
        return {
            "selected_profile": "fast",
            "reason": "Fast profile explicitly required",
            "factors": ["require_fast"]
        }

    goal_lower = goal.lower()

    # Selection heuristics from governance/runtime_profiles.v1.yaml
    fast_keywords = ["simple", "quick", "read", "analyze", "summarize", "list", "describe", "show"]
    hard_keywords = ["escalate", "fallback", "complex", "architecture", "critical", "error", "urgent"]

    fast_score = sum(1 for kw in fast_keywords if kw in goal_lower)
    hard_score = sum(1 for kw in hard_keywords if kw in goal_lower)

    factors = []
    if fast_score > hard_score:
        factors.append("simple_goal_keywords")
        selected = "fast"
    elif hard_score > 0:
        factors.append("complex_goal_keywords")
        selected = "hard"
    else:
        factors.append("default_to_balanced")
        selected = "balanced"

    return {
        "selected_profile": selected,
        "reason": f"Profile selected based on goal content",
        "factors": factors,
        "fast_score": fast_score,
        "hard_score": hard_score
    }


def build_inference_request(
    goal: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Build an inference request from a goal/task description.

    For Phase 1, this is primarily used by validators to construct test requests.
    The request includes the goal and optional context.

    Args:
        goal: Task description
        context: Optional task context dict

    Returns:
        dict with goal, context, and other metadata
    """
    return {
        "goal": goal,
        "context": context or {},
        "schema_version": "1.0"
    }


def route_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Route an inference request through the gateway.

    Selects the appropriate profile based on the goal and returns routing info.
    This is the primary entrypoint for inference request routing in Phase 1.

    Args:
        request: dict with goal, context, etc. (from build_inference_request)

    Returns:
        dict with selected_profile, backend, model, and reasoning
    """
    goal = request.get("goal", "")
    profile_selection = select_profile(goal)

    try:
        profiles = load_runtime_profiles()
        profile_config = profiles.get("profiles", {}).get(profile_selection["selected_profile"], {})

        return {
            "selected_profile": profile_selection["selected_profile"],
            "backend": profile_config.get("backend", "ollama"),
            "model": profile_config.get("model", "unknown"),
            "reasoning": profile_selection.get("reason", ""),
            "factors": profile_selection.get("factors", [])
        }
    except Exception as e:
        return {
            "selected_profile": profile_selection["selected_profile"],
            "backend": "unknown",
            "model": "unknown",
            "reasoning": f"Error retrieving profile config: {str(e)}",
            "factors": []
        }


# Export the canonical gateway and typed classes for use by runtime modules
__all__ = [
    "InferenceGateway",
    "GatewayRequest",
    "GatewayResponse",
    "ModelProfile",
    "get_profile",
    "load_runtime_profiles",
    "select_profile",
    "build_inference_request",
    "route_request",
]
