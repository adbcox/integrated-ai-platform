"""RM-UI-005 control-window state, routing, packet, and dashboard support."""
from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
ARTIFACT_ROOT = REPO_ROOT / "artifacts" / "rm_ui005"
ROADMAP_ROOT = REPO_ROOT / "docs" / "roadmap"
PLANNING_NEXT_PULL = REPO_ROOT / "artifacts" / "planning" / "next_pull.json"
PLANNING_BLOCKERS = REPO_ROOT / "artifacts" / "planning" / "blocker_registry.json"
RUNTIME_PROFILES = REPO_ROOT / "governance" / "runtime_profiles.v1.yaml"
VALIDATION_STATE = ARTIFACT_ROOT / "validation_state.json"
RM_UI005_ITEM = ROADMAP_ROOT / "items" / "RM-UI-005.yaml"

MANDATORY_AUTHORITY_FILES = [
    "CLAUDE.md",
    "AGENTS.md",
    "docs/agent/commands.md",
    "docs/agent/validation_order.md",
    "docs/roadmap/ROADMAP_AUTHORITY.md",
    "docs/roadmap/ROADMAP_STATUS_SYNC.md",
    "docs/roadmap/ROADMAP_MASTER.md",
    "docs/roadmap/ROADMAP_INDEX.md",
    "docs/roadmap/ACTIVE_ITEM_NORMALIZATION_AUDIT.md",
    "docs/roadmap/AUTONOMOUS_EXECUTION_OPERATING_MODE.md",
    "docs/roadmap/TARGET_SELECTION_POLICY.md",
    "docs/roadmap/AUTONOMOUS_READY_QUEUE.md",
    "docs/roadmap/items/RM-GOV-001.yaml",
    "docs/roadmap/items/RM-OPS-004.yaml",
    "docs/roadmap/items/RM-OPS-005.yaml",
    "docs/roadmap/items/RM-AUTO-001.yaml",
    "docs/roadmap/items/RM-GOV-009.yaml",
]

LANE_PRIORITY = ["control_window", "bugfix", "repo_audit", "bounded_feature"]
LANE_HINTS = {
    "control_window": ["control window", "dashboard", "rm-ui-005", "control-center", "control center", "orchestration", "openhands"],
    "bugfix": ["bug", "fix", "regression", "broken", "failure", "repair", "hotfix"],
    "repo_audit": ["audit", "consistency", "validate", "inventory", "status sync", "governance", "roadmap"],
    "bounded_feature": ["implement", "feature", "build", "add", "create", "support"],
}

LANE_PACKET_PRESETS: dict[str, dict[str, Any]] = {
    "control_window": {
        "bounded_scope": "Implement or evolve local execution control surfaces and orchestration adapters.",
        "allowed_files": ["framework/**", "bin/**", "tests/**", "docs/roadmap/**", "artifacts/**"],
        "forbidden_files": [".github/**", "node_modules/**", "venv/**"],
        "truth_surfaces": [
            "artifacts/planning/next_pull.json",
            "artifacts/planning/blocker_registry.json",
            "docs/roadmap/items/RM-UI-005.yaml",
            "artifacts/rm_ui005/control_window_state.json",
        ],
    },
    "bugfix": {
        "bounded_scope": "Apply bounded fix with explicit regression coverage and validation proof.",
        "allowed_files": ["framework/**", "runtime/**", "bin/**", "tests/**", "docs/**", "artifacts/**"],
        "forbidden_files": [".github/**", "node_modules/**", "venv/**"],
        "truth_surfaces": ["artifacts/rm_ui005/control_window_state.json", "artifacts/planning/blocker_registry.json"],
    },
    "repo_audit": {
        "bounded_scope": "Audit and reconcile roadmap/governance truth surfaces with deterministic outputs.",
        "allowed_files": ["docs/roadmap/**", "governance/**", "artifacts/**", "bin/**", "tests/**"],
        "forbidden_files": ["framework/**", "runtime/**", ".github/**"],
        "truth_surfaces": [
            "docs/roadmap/ROADMAP_STATUS_SYNC.md",
            "docs/roadmap/ROADMAP_MASTER.md",
            "docs/roadmap/ROADMAP_INDEX.md",
            "artifacts/planning/next_pull.json",
            "artifacts/planning/blocker_registry.json",
            "artifacts/rm_ui005/control_window_state.json",
        ],
    },
    "bounded_feature": {
        "bounded_scope": "Deliver bounded feature increment with scoped file set and validation evidence.",
        "allowed_files": ["framework/**", "runtime/**", "bin/**", "tests/**", "docs/**", "artifacts/**"],
        "forbidden_files": [".github/**", "node_modules/**", "venv/**"],
        "truth_surfaces": ["artifacts/rm_ui005/control_window_state.json", "artifacts/planning/blocker_registry.json"],
    },
}


@dataclass(frozen=True)
class RouteDecision:
    selected_lane: str
    score_by_lane: dict[str, int]
    reasons: list[str]
    repo_signals: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "selected_lane": self.selected_lane,
            "score_by_lane": self.score_by_lane,
            "reasons": self.reasons,
            "repo_signals": self.repo_signals,
        }


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _safe_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except Exception:
        return 0


def _run(cmd: list[str], *, cwd: Path | None = None) -> tuple[int, str, str]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd or REPO_ROOT),
        text=True,
        capture_output=True,
        check=False,
    )
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def git_branch_name(repo_root: Path = REPO_ROOT) -> str:
    code, out, _ = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_root)
    return out if code == 0 and out else "unknown"


def git_changed_files(repo_root: Path = REPO_ROOT) -> list[str]:
    code, out, _ = _run(["git", "status", "--porcelain"], cwd=repo_root)
    if code != 0 or not out:
        return []
    changed: list[str] = []
    for line in out.splitlines():
        if len(line) < 4:
            continue
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        changed.append(path.strip())
    return sorted(set(changed))


def _keyword_hits(text: str, keywords: list[str]) -> int:
    low = text.lower()
    return sum(1 for k in keywords if k in low)


def classify_lane(task_input: str, *, repo_root: Path = REPO_ROOT) -> RouteDecision:
    task = task_input.strip() or ""
    branch = git_branch_name(repo_root)
    changed = git_changed_files(repo_root)

    scores = {lane: _keyword_hits(task, hints) for lane, hints in LANE_HINTS.items()}
    reasons: list[str] = []

    if "control-window" in branch or "control_window" in branch or "rm-ui-005" in branch:
        scores["control_window"] += 2
        reasons.append(f"branch_signal={branch} -> control_window")

    if "bugfix" in branch or "hotfix" in branch:
        scores["bugfix"] += 2
        reasons.append(f"branch_signal={branch} -> bugfix")

    if changed:
        roadmap_or_governance = [p for p in changed if p.startswith("docs/roadmap/") or p.startswith("governance/")]
        if len(roadmap_or_governance) >= max(1, len(changed) // 2):
            # Treat repo-state as secondary unless the prompt explicitly sounds like an audit.
            audit_intent_hits = _keyword_hits(task, LANE_HINTS["repo_audit"])
            scores["repo_audit"] += 2 if audit_intent_hits > 0 else 1
            reasons.append("changed_file_signal=roadmap_or_governance_majority")

        if any(p.startswith("tests/") for p in changed) and any(p.startswith("framework/") or p.startswith("runtime/") for p in changed):
            scores["bugfix"] += 1
            reasons.append("changed_file_signal=code_plus_tests")

    if task:
        for lane, hints in LANE_HINTS.items():
            hits = [h for h in hints if h in task.lower()]
            if hits:
                reasons.append(f"keyword_signal[{lane}]={','.join(hits[:4])}")

    if scores["bounded_feature"] > 0 and scores["repo_audit"] == scores["bounded_feature"]:
        scores["bounded_feature"] += 1
        reasons.append("tie_breaker=explicit_feature_intent")

    selected = max(LANE_PRIORITY, key=lambda lane: (scores.get(lane, 0), -LANE_PRIORITY.index(lane)))
    if all(v == 0 for v in scores.values()):
        selected = "bounded_feature"
        reasons.append("fallback=bounded_feature_no_signals")

    return RouteDecision(
        selected_lane=selected,
        score_by_lane=scores,
        reasons=reasons,
        repo_signals={
            "branch": branch,
            "changed_files_count": len(changed),
            "changed_files": changed[:50],
        },
    )


def _load_runtime_profiles() -> dict[str, Any]:
    if not RUNTIME_PROFILES.exists():
        return {}
    try:
        data = yaml.safe_load(RUNTIME_PROFILES.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data.get("profiles", {}) if isinstance(data, dict) else {}


def _profile_for_lane(lane: str) -> str:
    if lane == "bugfix":
        return "balanced"
    if lane == "repo_audit":
        return "fast"
    if lane == "control_window":
        return "hard"
    return "balanced"


def build_context_pressure(
    *,
    lane: str,
    preload_files: list[str],
    drop_candidates_seed: list[str],
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    profiles = _load_runtime_profiles()
    profile_name = _profile_for_lane(lane)
    profile = profiles.get(profile_name, {}) if isinstance(profiles, dict) else {}
    token_limit = int(profile.get("context_window_tokens", 4096))

    changed_files = git_changed_files(repo_root)
    must_retain = sorted(set(MANDATORY_AUTHORITY_FILES + preload_files[:8]))
    context_files = sorted(set(must_retain + preload_files + changed_files[:30]))

    contributors: list[dict[str, Any]] = []
    total_tokens = 0
    for rel in context_files:
        fpath = repo_root / rel
        size = _safe_size(fpath)
        est_tokens = max(1, size // 4) if size else 0
        total_tokens += est_tokens
        contributors.append({"path": rel, "bytes": size, "estimated_tokens": est_tokens})

    contributors.sort(key=lambda item: item["estimated_tokens"], reverse=True)
    ratio = (total_tokens / token_limit) if token_limit else 1.0
    if ratio >= 0.95:
        risk = "high"
    elif ratio >= 0.75:
        risk = "moderate"
    else:
        risk = "low"

    safe_to_drop = [
        item["path"]
        for item in contributors
        if item["path"] not in must_retain
    ]
    for seed in drop_candidates_seed:
        if seed not in must_retain and seed not in safe_to_drop:
            safe_to_drop.append(seed)

    narrowing_recommendations: list[str] = []
    if risk == "high":
        narrowing_recommendations.append(
            "High overflow risk: drop top safe-to-drop context files before execution."
        )
        narrowing_recommendations.append(
            "Run lane-specific packet with minimal preload and re-add files incrementally."
        )
    elif risk == "moderate":
        narrowing_recommendations.append(
            "Moderate overflow risk: prune non-authoritative docs and large generated artifacts."
        )
    else:
        narrowing_recommendations.append(
            "Context risk low: keep must-retain files, but drop unrelated changed files to reduce latency."
        )
    if len(changed_files) > 25:
        narrowing_recommendations.append(
            "Large changed-file set: filter packet scope to objective-adjacent files before running Aider."
        )
    if safe_to_drop:
        narrowing_recommendations.append(
            f"Start drops with: {', '.join(safe_to_drop[:3])}"
        )

    return {
        "profile": profile_name,
        "model": profile.get("model", "unknown"),
        "token_limit": token_limit,
        "estimated_context_tokens": total_tokens,
        "context_ratio": round(ratio, 3),
        "overflow_risk": risk,
        "top_context_contributors": contributors[:8],
        "must_retain_context": must_retain,
        "safe_to_drop_context": safe_to_drop[:20],
        "narrowing_recommendations": narrowing_recommendations,
        "files_in_context": context_files,
        "files_changed": changed_files,
    }


def build_aider_packet(task_input: str, decision: RouteDecision, *, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    lane = decision.selected_lane
    preset = LANE_PACKET_PRESETS[lane]
    aider_class_by_lane = {
        "control_window": "targeted-feature-patch",
        "bounded_feature": "targeted-feature-patch",
        "bugfix": "bugfix-small",
        "repo_audit": "docs-sync",
    }

    preload = sorted(set(MANDATORY_AUTHORITY_FILES + [
        "artifacts/planning/next_pull.json",
        "artifacts/planning/blocker_registry.json",
    ]))

    drop_seed = [
        "docs/level10-roadmap.md",
        "docs/version15-master-roadmap.md",
        "artifacts/integration_phase1_execution_report.md",
    ]
    context = build_context_pressure(lane=lane, preload_files=preload, drop_candidates_seed=drop_seed, repo_root=repo_root)

    validations = [
        {"id": "planning_surfaces_present", "command": "internal:file-existence-check", "required": True},
        {"id": "route_decision_materialized", "command": "internal:route-check", "required": True},
        {"id": "make_check", "command": "make check", "required": True},
        {"id": "make_quick", "command": "make quick", "required": True},
        {"id": "make_test_offline", "command": "make test-offline", "required": True},
    ]

    completion_criteria = {
        "substep_complete": [
            "deterministic route decision emitted",
            "aider run packet emitted",
            "blocker and next-target state surfaced",
        ],
        "bounded_slice_complete": [
            "required validations pass",
            "required artifacts emitted",
            "completion ladder rendered",
        ],
        "item_complete": [
            "Canonical RM-UI-005 item completion contract is satisfied (all planned slices and DoD evidence complete)",
            "Aider and OpenHands execution surfaces remain wired into the same governed control model",
        ],
        "blocker_chain_cleared": [
            "blocker chain reports no active true blockers for selected target",
        ],
        "objective_achieved": [
            "all completion ladder levels pass",
        ],
    }

    return {
        "selected_lane": lane,
        "objective": task_input,
        "aider_execution": {
            "runner": "bin/aider_task_runner.py",
            "task_class": aider_class_by_lane[lane],
            "command_template": (
                "python3 bin/aider_task_runner.py --class {task_class} --name rm-ui-005-{lane} "
                "--objective \"{objective}\" --file framework/rm_ui005_control_window.py "
                "--file tests/test_rm_ui005_router_packet.py"
            ).format(task_class=aider_class_by_lane[lane], lane=lane, objective=task_input),
        },
        "bounded_scope": preset["bounded_scope"],
        "allowed_files": preset["allowed_files"],
        "forbidden_files": preset["forbidden_files"],
        "preload_context_files": preload,
        "drop_candidates": context["safe_to_drop_context"],
        "validations_to_run": validations,
        "completion_criteria": completion_criteria,
        "truth_surfaces_to_update": preset["truth_surfaces"],
        "stop_conditions": [
            "validation failure requiring rollback",
            "forbidden-file modification would be required",
            "scope exceeds bounded lane contract",
        ],
        "context_pressure": context,
    }


def _load_planning_state() -> dict[str, Any]:
    next_pull = _read_json(PLANNING_NEXT_PULL, {})
    blockers = _read_json(PLANNING_BLOCKERS, {})

    chosen = next_pull.get("chosen_next_item")
    candidates = next_pull.get("next_pull_candidates") or []
    nodes = next_pull.get("nodes") or {}

    why_selected = "queue empty"
    if chosen and isinstance(nodes, dict) and chosen in nodes:
        reasons = nodes[chosen].get("reasons") or []
        why_selected = "; ".join(reasons) if reasons else "eligible_by_selector"
    elif candidates:
        first = candidates[0]
        why_selected = "; ".join(first.get("reasons", [])) or "eligible_candidate_present"
    else:
        status = next_pull.get("status", "unknown")
        why_selected = f"selector_status={status}"

    def _blocker_id(item: Any) -> str:
        if isinstance(item, dict):
            return str(item.get("id", "unknown"))
        return str(item)

    def _blocker_reason(item: Any) -> str:
        if isinstance(item, dict):
            reasons = item.get("reasons", "")
            if isinstance(reasons, list):
                return ",".join(str(r) for r in reasons)
            return str(reasons)
        return "placeholder_state_conflict"

    blocker_chain: list[dict[str, Any]] = []
    for item in blockers.get("true_blockers", []):
        blocker_chain.append({
            "id": _blocker_id(item),
            "reason": _blocker_reason(item),
            "class": "true_blocker",
        })
    for item in blockers.get("blocked_external_dependency_items", []):
        blocker_chain.append({
            "id": _blocker_id(item),
            "reason": _blocker_reason(item),
            "class": "external_dependency",
        })
    for item in blockers.get("blocked_placeholder_items", []):
        blocker_chain.append({
            "id": _blocker_id(item),
            "reason": _blocker_reason(item),
            "class": "placeholder",
        })

    return {
        "next_eligible_target": chosen,
        "next_candidates": candidates[:5],
        "why_selected": why_selected,
        "blocker_chain": blocker_chain,
        "blocker_summary": blockers.get("summary", {}),
        "selector_status": next_pull.get("status", "unknown"),
    }


def _internal_validation_status(packet: dict[str, Any], planning: dict[str, Any]) -> dict[str, str]:
    statuses: dict[str, str] = {}
    statuses["planning_surfaces_present"] = (
        "pass" if PLANNING_NEXT_PULL.exists() and PLANNING_BLOCKERS.exists() else "fail"
    )
    statuses["route_decision_materialized"] = (
        "pass" if packet.get("selected_lane") in LANE_PACKET_PRESETS else "fail"
    )
    statuses["queue_or_blocker_visible"] = "pass" if planning.get("selector_status") else "fail"
    return statuses


def load_validation_state() -> dict[str, Any]:
    return _read_json(VALIDATION_STATE, {"generated_at": None, "results": {}})


def run_repo_validations(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    commands = {
        "make_check": ["make", "check"],
        "make_quick": ["make", "quick"],
        "make_test_offline": ["make", "test-offline"],
    }
    results: dict[str, Any] = {}
    for key, cmd in commands.items():
        code, out, err = _run(cmd, cwd=repo_root)
        results[key] = {
            "status": "pass" if code == 0 else "fail",
            "exit_code": code,
            "stdout_tail": "\n".join(out.splitlines()[-20:]),
            "stderr_tail": "\n".join(err.splitlines()[-20:]),
            "command": " ".join(cmd),
        }

    payload = {"generated_at": _utc_now(), "results": results}
    VALIDATION_STATE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def build_validation_panel(packet: dict[str, Any], planning: dict[str, Any]) -> dict[str, Any]:
    required = packet.get("validations_to_run", [])
    internal = _internal_validation_status(packet, planning)
    cached = load_validation_state().get("results", {})

    evaluation: list[dict[str, Any]] = []
    for item in required:
        vid = item["id"]
        if vid in internal:
            state = internal[vid]
        elif vid in cached:
            state = cached[vid].get("status", "unknown")
        else:
            state = "pending"
        evaluation.append({"id": vid, "command": item.get("command"), "status": state})

    return {"required_validations": evaluation}


def build_artifact_panel(packet: dict[str, Any], *, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    required = sorted(set(packet.get("truth_surfaces_to_update", []) + [
        "artifacts/planning/next_pull.json",
        "artifacts/planning/blocker_registry.json",
        "artifacts/rm_ui005/control_window_state.json",
    ]))
    emitted = [p for p in required if (repo_root / p).exists()]
    missing = [p for p in required if p not in emitted]
    return {
        "required_artifacts": required,
        "emitted_artifacts": emitted,
        "missing_evidence": missing,
    }


def _canonical_rm_ui005_item_contract_satisfied() -> bool:
    if not RM_UI005_ITEM.exists():
        return False
    try:
        item = yaml.safe_load(RM_UI005_ITEM.read_text(encoding="utf-8"))
    except Exception:
        return False
    if not isinstance(item, dict):
        return False
    if item.get("status") != "completed":
        return False
    completion_contract = (
        item.get("execution_contract", {}).get("completion_contract", {})
        if isinstance(item.get("execution_contract"), dict)
        else {}
    )
    item_complete_when = completion_contract.get("item_complete_when")
    has_item_contract = isinstance(item_complete_when, list) and len(item_complete_when) > 0
    explicit_evidence = bool(item.get("validation", {}).get("item_complete_evidence", False))
    return has_item_contract and explicit_evidence


def _openhands_contract_satisfied(openhands: dict[str, Any]) -> bool:
    # RM-UI-005 contract treats OpenHands as optional local surface; host runtime readiness
    # (for example docker availability) is not required for canonical item completion.
    authority_ok = openhands.get("authority_model") == "subordinate_to_control_window_route_and_completion_contract"
    dry_run_ok = bool(openhands.get("dry_run_ready", False))
    selected = openhands.get("selected_plan", {})
    command_ok = isinstance(selected.get("command"), list) and len(selected.get("command")) > 0
    return authority_ok and dry_run_ok and command_ok


def build_completion_ladder(
    *,
    validation_panel: dict[str, Any],
    artifact_panel: dict[str, Any],
    planning: dict[str, Any],
    openhands_contract_satisfied: bool,
    canonical_item_contract_satisfied: bool,
) -> dict[str, Any]:
    validation_statuses = [entry["status"] for entry in validation_panel.get("required_validations", [])]
    all_required_validations_pass = bool(validation_statuses) and all(state == "pass" for state in validation_statuses)

    substep_complete = any(state in {"pass", "pending"} for state in validation_statuses)
    bounded_slice_complete = all_required_validations_pass and not artifact_panel.get("missing_evidence")
    item_complete = bounded_slice_complete and openhands_contract_satisfied and canonical_item_contract_satisfied
    blocker_chain_cleared = len(planning.get("blocker_chain", [])) == 0
    objective_achieved = item_complete and blocker_chain_cleared

    return {
        "substep_complete": substep_complete,
        "bounded_slice_complete": bounded_slice_complete,
        "item_complete": item_complete,
        "blocker_chain_cleared": blocker_chain_cleared,
        "objective_achieved": objective_achieved,
    }


def build_openhands_plan(*, mode: str = "docker_web", repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    from framework.rm_ui005_openhands import build_openhands_launch_plan, build_openhands_mode_matrix

    selected = build_openhands_launch_plan(mode=mode, repo_root=repo_root)
    matrix = build_openhands_mode_matrix(repo_root=repo_root)
    dry_run_ready = bool(selected.get("command")) and mode in matrix
    integration_ready = bool(selected.get("ready", False)) and dry_run_ready
    return {
        "selected_mode": mode,
        "selected_plan": selected,
        "available_modes": matrix,
        "ready": selected.get("ready", False),
        "dry_run_ready": dry_run_ready,
        "integration_ready": integration_ready,
        "sandbox_posture": selected.get("sandbox_posture", "unknown"),
        "authority_model": selected.get("authority_model"),
    }


def build_control_window_state(
    *,
    task_input: str,
    objective: str | None = None,
    repo_root: Path = REPO_ROOT,
    openhands_mode: str = "docker_web",
) -> dict[str, Any]:
    objective_text = objective or task_input or "RM-UI-005 local control window first slice"
    decision = classify_lane(task_input=task_input, repo_root=repo_root)
    packet = build_aider_packet(task_input=objective_text, decision=decision, repo_root=repo_root)
    planning = _load_planning_state()
    openhands = build_openhands_plan(mode=openhands_mode, repo_root=repo_root)
    validation_panel = build_validation_panel(packet, planning)
    artifact_panel = build_artifact_panel(packet, repo_root=repo_root)
    canonical_item_contract_satisfied = _canonical_rm_ui005_item_contract_satisfied()
    completion_ladder = build_completion_ladder(
        validation_panel=validation_panel,
        artifact_panel=artifact_panel,
        planning=planning,
        openhands_contract_satisfied=_openhands_contract_satisfied(openhands),
        canonical_item_contract_satisfied=canonical_item_contract_satisfied,
    )

    state = {
        "generated_at": _utc_now(),
        "current_objective": objective_text,
        "current_lane": decision.selected_lane,
        "current_branch": git_branch_name(repo_root),
        "route_decision": decision.to_dict(),
        "aider_run_packet": packet,
        "planning": planning,
        "context_token_pressure": packet.get("context_pressure", {}),
        "validation_panel": validation_panel,
        "artifact_panel": artifact_panel,
        "completion_ladder": completion_ladder,
        "openhands": openhands,
    }
    return state


def emit_control_window_state(state: dict[str, Any], *, artifact_root: Path = ARTIFACT_ROOT) -> Path:
    artifact_root.mkdir(parents=True, exist_ok=True)
    out = artifact_root / "control_window_state.json"
    out.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return out


def render_html(state: dict[str, Any]) -> str:
    def _list(items: list[str]) -> str:
        if not items:
            return "<li>none</li>"
        return "".join(f"<li><code>{i}</code></li>" for i in items)

    validations = state["validation_panel"]["required_validations"]
    validation_rows = "".join(
        f"<tr><td><code>{v['id']}</code></td><td><code>{v['command']}</code></td><td>{v['status']}</td></tr>"
        for v in validations
    )

    blockers = state["planning"]["blocker_chain"]
    blocker_rows = "".join(
        f"<tr><td><code>{b['id']}</code></td><td>{b['class']}</td><td>{b['reason']}</td></tr>"
        for b in blockers
    ) or "<tr><td colspan='3'>no active blockers</td></tr>"

    top_context = state["context_token_pressure"].get("top_context_contributors", [])
    context_rows = "".join(
        f"<tr><td><code>{c['path']}</code></td><td>{c['estimated_tokens']}</td><td>{c['bytes']}</td></tr>"
        for c in top_context
    )
    context_recs = _list(state["context_token_pressure"].get("narrowing_recommendations", []))

    ladder = state["completion_ladder"]
    openhands = state["openhands"]
    openhands_modes = openhands.get("available_modes", {})
    openhands_rows = "".join(
        f"<tr><td><code>{mode}</code></td><td>{plan.get('ready')}</td><td>{plan.get('sandbox_posture')}</td><td><code>{' '.join(plan.get('command', []))}</code></td></tr>"
        for mode, plan in openhands_modes.items()
    ) or "<tr><td colspan='4'>no modes available</td></tr>"

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset=\"utf-8\" />
<title>RM-UI-005 Control Window</title>
<style>
body {{ font-family: Arial, sans-serif; background: #f4f6f8; margin: 0; padding: 16px; }}
.container {{ max-width: 1400px; margin: 0 auto; }}
.grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
.panel {{ background: #fff; border: 1px solid #d6dbe1; border-radius: 6px; padding: 12px; }}
h1, h2 {{ margin: 0 0 8px 0; }}
table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
th, td {{ border: 1px solid #d6dbe1; padding: 6px; text-align: left; vertical-align: top; }}
code {{ background: #eef2f6; padding: 1px 4px; border-radius: 3px; }}
.badge {{ display: inline-block; padding: 2px 8px; border-radius: 12px; background: #e6edf5; margin-right: 6px; }}
</style>
</head>
<body>
<div class=\"container\">
  <h1>RM-UI-005 Local Execution Control Window</h1>
  <p>Generated: {state['generated_at']}</p>
  <div class=\"panel\">
    <div><span class=\"badge\">objective</span> {state['current_objective']}</div>
    <div><span class=\"badge\">lane</span> <code>{state['current_lane']}</code></div>
    <div><span class=\"badge\">branch</span> <code>{state['current_branch']}</code></div>
    <div><span class=\"badge\">next governed target</span> <code>{state['planning'].get('next_eligible_target') or 'none'}</code></div>
    <div><span class=\"badge\">why selected</span> {state['planning'].get('why_selected')}</div>
  </div>

  <div class=\"grid\">
    <div class=\"panel\">
      <h2>Routing Decision</h2>
      <pre>{json.dumps(state['route_decision'], indent=2)}</pre>
    </div>
    <div class=\"panel\">
      <h2>Aider Packet</h2>
      <pre>{json.dumps(state['aider_run_packet'], indent=2)}</pre>
    </div>

    <div class=\"panel\">
      <h2>Blocker Chain</h2>
      <table><thead><tr><th>ID</th><th>Class</th><th>Reason</th></tr></thead><tbody>{blocker_rows}</tbody></table>
    </div>
    <div class=\"panel\">
      <h2>Context / Token Pressure</h2>
      <div>profile: <code>{state['context_token_pressure'].get('profile')}</code></div>
      <div>model: <code>{state['context_token_pressure'].get('model')}</code></div>
      <div>estimated tokens: {state['context_token_pressure'].get('estimated_context_tokens')}</div>
      <div>limit: {state['context_token_pressure'].get('token_limit')}</div>
      <div>overflow risk: <strong>{state['context_token_pressure'].get('overflow_risk')}</strong></div>
      <table><thead><tr><th>File</th><th>Est Tokens</th><th>Bytes</th></tr></thead><tbody>{context_rows}</tbody></table>
      <h3>Drop Candidates</h3>
      <ul>{_list(state['context_token_pressure'].get('safe_to_drop_context', []))}</ul>
      <h3>Narrowing Recommendations</h3>
      <ul>{context_recs}</ul>
    </div>

    <div class=\"panel\">
      <h2>Validation Results</h2>
      <table><thead><tr><th>ID</th><th>Command</th><th>Status</th></tr></thead><tbody>{validation_rows}</tbody></table>
    </div>
    <div class=\"panel\">
      <h2>Artifact Outputs</h2>
      <div>required:</div><ul>{_list(state['artifact_panel']['required_artifacts'])}</ul>
      <div>emitted:</div><ul>{_list(state['artifact_panel']['emitted_artifacts'])}</ul>
      <div>missing evidence:</div><ul>{_list(state['artifact_panel']['missing_evidence'])}</ul>
    </div>

    <div class=\"panel\">
      <h2>Completion Ladder</h2>
      <table>
        <tr><th>Substep Complete</th><td>{ladder['substep_complete']}</td></tr>
        <tr><th>Bounded Slice Complete</th><td>{ladder['bounded_slice_complete']}</td></tr>
        <tr><th>Item Complete</th><td>{ladder['item_complete']}</td></tr>
        <tr><th>Blocker Chain Cleared</th><td>{ladder['blocker_chain_cleared']}</td></tr>
        <tr><th>Objective Achieved</th><td>{ladder['objective_achieved']}</td></tr>
      </table>
    </div>
    <div class=\"panel\">
      <h2>OpenHands Local Path</h2>
      <div>selected mode: <code>{openhands.get('selected_mode')}</code></div>
      <div>selected runtime ready: <strong>{openhands.get('ready')}</strong></div>
      <div>integration ready: <strong>{openhands.get('integration_ready')}</strong></div>
      <table><thead><tr><th>Mode</th><th>Ready</th><th>Sandbox</th><th>Command</th></tr></thead><tbody>{openhands_rows}</tbody></table>
    </div>
  </div>
</div>
</body>
</html>
"""


__all__ = [
    "RouteDecision",
    "build_control_window_state",
    "build_aider_packet",
    "build_context_pressure",
    "classify_lane",
    "emit_control_window_state",
    "render_html",
    "run_repo_validations",
]
