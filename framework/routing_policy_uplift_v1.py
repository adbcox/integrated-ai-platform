"""Routing policy uplift surface for Phase 4 self-sufficiency uplift (P4-01).

Maps task_class / difficulty to a selected model profile and retry posture.
References Phase 1 model profile names from governance/model_profiles_contract.v1.yaml.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


# Phase 1 canonical profile names (from model_profiles_contract.v1.yaml)
PROFILE_LOCAL_FAST = "local_fast"       # qwen2.5-coder:14b via Ollama
PROFILE_LOCAL_HARD = "local_hard"       # deepseek-coder-v2 via Ollama
PROFILE_LOCAL_SMART = "local_smart"     # 32B model via Ollama
PROFILE_REMOTE_ASSIST = "remote_assist" # Claude remote fallback

DIFFICULTY_LOW = "low"
DIFFICULTY_MEDIUM = "medium"
DIFFICULTY_HIGH = "high"


@dataclass
class RoutingDecisionV1:
    task_class: str
    difficulty: str
    selected_profile: str
    retry_budget: int
    retry_posture: str   # conservative | standard | aggressive
    rationale: str

    def to_dict(self) -> dict:
        return {
            "task_class": self.task_class,
            "difficulty": self.difficulty,
            "selected_profile": self.selected_profile,
            "retry_budget": self.retry_budget,
            "retry_posture": self.retry_posture,
            "rationale": self.rationale,
        }


_ROUTING_TABLE: dict = {
    # (task_class, difficulty) -> (profile, retry_budget, posture)
    ("bug_fix", DIFFICULTY_LOW):         (PROFILE_LOCAL_FAST,   1, "conservative"),
    ("bug_fix", DIFFICULTY_MEDIUM):      (PROFILE_LOCAL_HARD,   2, "standard"),
    ("bug_fix", DIFFICULTY_HIGH):        (PROFILE_LOCAL_SMART,  3, "aggressive"),
    ("narrow_feature", DIFFICULTY_LOW):  (PROFILE_LOCAL_FAST,   1, "conservative"),
    ("narrow_feature", DIFFICULTY_MEDIUM): (PROFILE_LOCAL_HARD, 2, "standard"),
    ("narrow_feature", DIFFICULTY_HIGH): (PROFILE_LOCAL_SMART,  3, "aggressive"),
    ("reporting_helper", DIFFICULTY_LOW):    (PROFILE_LOCAL_FAST, 1, "conservative"),
    ("reporting_helper", DIFFICULTY_MEDIUM): (PROFILE_LOCAL_FAST, 2, "standard"),
    ("reporting_helper", DIFFICULTY_HIGH):   (PROFILE_LOCAL_HARD, 2, "standard"),
    ("test_addition", DIFFICULTY_LOW):   (PROFILE_LOCAL_FAST,   1, "conservative"),
    ("test_addition", DIFFICULTY_MEDIUM): (PROFILE_LOCAL_HARD,  2, "standard"),
    ("test_addition", DIFFICULTY_HIGH):  (PROFILE_LOCAL_HARD,   2, "standard"),
}

_DEFAULT_ROUTE = (PROFILE_REMOTE_ASSIST, 2, "standard")


class RoutingPolicyUpliftV1:
    def decide(
        self,
        task_class: str,
        difficulty: str = DIFFICULTY_MEDIUM,
        override_profile: Optional[str] = None,
    ) -> RoutingDecisionV1:
        key = (task_class, difficulty)
        profile, budget, posture = _ROUTING_TABLE.get(key, _DEFAULT_ROUTE)

        if override_profile is not None:
            profile = override_profile
            rationale = f"Profile overridden to {profile}; base difficulty={difficulty}"
        else:
            rationale = (
                f"Routed {task_class}/{difficulty} → {profile} "
                f"(retry_budget={budget}, posture={posture})"
            )

        return RoutingDecisionV1(
            task_class=task_class,
            difficulty=difficulty,
            selected_profile=profile,
            retry_budget=budget,
            retry_posture=posture,
            rationale=rationale,
        )
