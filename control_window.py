from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field


LaneName = Literal["bugfix", "bounded_feature", "control_window", "repo_audit"]


CANONICAL_TRUTH_SURFACES = [
    "docs/roadmap/ROADMAP_AUTHORITY.md",
    "docs/roadmap/ROADMAP_STATUS_SYNC.md",
    "docs/roadmap/ROADMAP_MASTER.md",
    "docs/roadmap/ROADMAP_INDEX.md",
    "docs/roadmap/ACTIVE_ITEM_NORMALIZATION_AUDIT.md",
    "docs/roadmap/AUTONOMOUS_EXECUTION_OPERATING_MODE.md",
    "docs/roadmap/TARGET_SELECTION_POLICY.md",
    "docs/roadmap/AUTONOMOUS_READY_QUEUE.md",
]

REQUIRED_ROUTE_FILES = [
    "docs/roadmap/ITEMS/RM-UI-005.md",
    "docs/roadmap/ITEMS/RM-GOV-001.md",
    "docs/roadmap/ITEMS/RM-OPS-004.md",
    "docs/roadmap/ITEMS/RM-OPS-005.md",
    "docs/roadmap/ITEMS/RM-AUTO-001.md",
    "docs/roadmap/ITEMS/RM-GOV-009.md",
]

OPTIONAL_ARTIFACT_FILES = [
    "artifacts/planning/next_pull.json",
    "artifacts/planning/blocker_registry.json",
]

LANE_TO_AIDER_CLASS = {
    "bugfix": "bugfix-small",
    "bounded_feature": "targeted-feature-patch",
    "control_window": "docs-sync",
    "repo_audit": "docs-sync",
}

LANE_VALIDATIONS = {
    "bugfix": ["make quick", "make test-changed-offline"],
    "bounded_feature": ["make quick", "make test-changed-offline"],
    "control_window": ["make quick"],
    "repo_audit": ["make quick"],
}

LANE_STOP_CONDITIONS = {
    "bugfix": [
        "stop when the named failure is no longer reproducible",
        "stop when required validations pass",
        "stop when the fix expands beyond the bounded bug surface",
    ],
    "bounded_feature": [
        "stop when the bounded slice is implemented and validations pass",
        "stop when truth-surface updates remain unmet after code changes",
        "stop when the change expands beyond the allowed files or adjacent tests/docs",
    ],
    "control_window": [
        "stop when completion truth has been reconciled with on-disk evidence",
        "stop if narrative claims exceed file/artifact evidence",
        "stop when adjacent implementation would become unrelated roadmap work",
    ],
    "repo_audit": [
        "stop after the bounded audit summary and blocker chain are emitted",
        "stop if a write would exceed audit or evidence-surface scope",
        "stop when unresolved authority conflicts require escalation",
    ],
}

PREFERRED_ACTIVE_ORDER = [
    "RM-UI-005",
    "RM-AUTO-001",
    "RM-GOV-001",
    "RM-OPS-005",
    "RM-OPS-004",
    "RM-INV-002",
]

ROUTE_KEYWORDS = {
    "bugfix": [
        "bug", "fix", "failing", "failure", "regression", "traceback", "error",
        "repair", "broken", "panic", "exception", "defect",
    ],
    "control_window": [
        "control window", "validate", "validation", "closeout", "actually complete",
        "truth", "closure", "blocker chain", "status contradiction",
    ],
    "repo_audit": [
        "audit", "scan", "review repo", "drift", "mismatch", "inventory",
        "naming", "duplicate logic", "read-only",
    ],
    "bounded_feature": [
        "build", "implement", "add", "feature", "dashboard", "panel", "route",
        "packet", "ui", "surface", "support", "first slice",
    ],
}


class RouteRequest(BaseModel):
    objective: str = Field(..., min_length=1)
    files: list[str] = Field(default_factory=list)
    changed_files: list[str] = Field(default_factory=list)
    current_item: str = "RM-UI-005"
    branch: str = "main"
    lane_hint: str | None = None


class LaneCandidate(BaseModel):
    lane: LaneName
    score: int
    reason: str


class RouteDecision(BaseModel):
    selected_lane: LaneName
    rationale: list[str]
    competing_lanes: list[LaneCandidate]
    machine_route: dict[str, Any]


class ContextPressure(BaseModel):
    estimated_tokens: int
    estimated_limit: int
    overflow_risk: str
    in_context_files: list[str]
    changed_files: list[str]
    top_context_contributors: list[dict[str, Any]]
    must_retain: list[str]
    safe_to_drop: list[str]
    recommended_drop_candidates: list[str]


class ValidationState(BaseModel):
    required_validations: list[dict[str, Any]]
    required_artifacts: list[str]
    emitted_artifacts: list[str]
    missing_evidence: list[str]


class CompletionLadder(BaseModel):
    substep_complete: bool
    bounded_slice_complete: bool
    item_complete: bool
    blocker_chain_cleared: bool
    objective_achieved: bool
    reasons: list[str]


class AiderRunPacket(BaseModel):
    packet_version: str = "rm-ui-005.v1"
    selected_lane: LaneName
    aider_task_class: str
    objective: str
    bounded_scope: str
    allowed_files: list[str]
    forbidden_files: list[str]
    preload_files: list[str]
    drop_candidates: list[str]
    validations_to_run: list[str]
    completion_criteria: list[str]
    truth_surfaces_to_update: list[str]
    stop_conditions: list[str]
    packet_command: str
    packet_payload: dict[str, Any]


class OpenHandsPlan(BaseModel):
    mode: Literal["cli", "web", "serve", "docker-serve"]
    command: str
    repo_mount_enabled: bool
    port: int | None = None
    subordinate_to_same_truth_model: bool = True
    notes: list[str]


class NextTargetState(BaseModel):
    selected_item: str
    selected_reason: str
    blocked_items: list[dict[str, str]]
    competing_items: list[str]


class DashboardSnapshot(BaseModel):
    current_objective: str
    current_item: str
    branch: str
    blocker_chain: list[str]
    next_target: NextTargetState
    context_pressure: ContextPressure
    validations: ValidationState
    completion_ladder: CompletionLadder
    route_decision: RouteDecision
    aider_packet: AiderRunPacket
    openhands_paths: list[OpenHandsPlan]
    artifact_outputs: list[str]
    truth_surfaces_read: list[str]


def _read_text(repo_root: Path, relpath: str) -> str:
    path = repo_root / relpath
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _read_json(repo_root: Path, relpath: str) -> Any:
    path = repo_root / relpath
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_status_sync(text: str) -> dict[str, str]:
    status: dict[str, str] = {}
    section = ""
    for raw_line in (text or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("## "):
            section = line.lower()
            continue
        match = re.match(r"- `([^`]+)`\s+—\s+(.+)$", line)
        if not match:
            continue
        item_id, state = match.groups()
        if "archived / completed items" in section:
            status[item_id] = "archived"
        elif "closed / completed items" in section:
            status[item_id] = "completed"
        elif "active items remaining" in section:
            status[item_id] = "active"
        else:
            status[item_id] = state.strip()
    return status


def _parse_normalization_audit(text: str) -> dict[str, list[str]]:
    normalized: list[str] = []
    blocked: list[str] = []
    mode = ""
    for raw_line in (text or "").splitlines():
        line = raw_line.strip()
        if line.startswith("### Fully normalized active items"):
            mode = "normalized"
            continue
        if line.startswith("### Explicit blocked placeholders"):
            mode = "blocked"
            continue
        match = re.match(r"- `([^`]+)`", line)
        if not match:
            continue
        item_id = match.group(1)
        if mode == "normalized":
            normalized.append(item_id)
        elif mode == "blocked":
            blocked.append(item_id)
    return {"normalized": normalized, "blocked": blocked}


def _current_branch(repo_root: Path) -> str:
    head = repo_root / ".git" / "HEAD"
    if not head.exists():
        return "main"
    text = head.read_text(encoding="utf-8").strip()
    if text.startswith("ref: refs/heads/"):
        return text.rsplit("/", 1)[-1]
    return "detached"


def _file_token_estimate(path: Path) -> int:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return 0
    return max(1, len(text) // 4)


def estimate_context_pressure(repo_root: Path, files: list[str], changed_files: list[str], lane: LaneName) -> ContextPressure:
    unique_files: list[str] = []
    for rel in files:
        if rel not in unique_files:
            unique_files.append(rel)

    contributors: list[dict[str, Any]] = []
    must_retain: list[str] = []
    safe_to_drop: list[str] = []

    for rel in unique_files:
        path = repo_root / rel
        tokens = _file_token_estimate(path)
        contributors.append({
            "path": rel,
            "estimated_tokens": tokens,
            "exists": path.exists(),
        })
        if rel.startswith("docs/roadmap/") or rel in changed_files:
            must_retain.append(rel)
        else:
            safe_to_drop.append(rel)

    contributors.sort(key=lambda item: item["estimated_tokens"], reverse=True)
    estimated_tokens = sum(item["estimated_tokens"] for item in contributors)

    estimated_limit = 32000
    if lane == "bounded_feature":
        estimated_limit = 64000
    overflow_ratio = estimated_tokens / float(estimated_limit or 1)
    if overflow_ratio >= 0.9:
        risk = "high"
    elif overflow_ratio >= 0.7:
        risk = "medium"
    else:
        risk = "low"

    recommended_drop = [item["path"] for item in contributors if item["path"] in safe_to_drop][:3]

    return ContextPressure(
        estimated_tokens=estimated_tokens,
        estimated_limit=estimated_limit,
        overflow_risk=risk,
        in_context_files=unique_files,
        changed_files=changed_files,
        top_context_contributors=contributors[:5],
        must_retain=must_retain,
        safe_to_drop=safe_to_drop,
        recommended_drop_candidates=recommended_drop,
    )


def detect_route(request: RouteRequest, repo_root: Path) -> RouteDecision:
    objective_l = request.objective.lower()
    scores: dict[LaneName, int] = {
        "bugfix": 0,
        "bounded_feature": 0,
        "control_window": 0,
        "repo_audit": 0,
    }
    reasons: dict[LaneName, list[str]] = {lane: [] for lane in scores}

    if request.lane_hint and request.lane_hint in scores:
        lane_hint = request.lane_hint
        scores[lane_hint] += 6
        reasons[lane_hint].append(f"explicit lane_hint matched {lane_hint}")

    for lane, keywords in ROUTE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in objective_l:
                scores[lane] += 2
                reasons[lane].append(f"objective contains '{keyword}'")

    if request.files:
        doc_count = sum(1 for item in request.files if item.startswith("docs/") or item.endswith(".md"))
        test_count = sum(1 for item in request.files if item.startswith("tests/"))
        if test_count:
            scores["bugfix"] += 2
            reasons["bugfix"].append("target files include tests")
        if doc_count == len(request.files):
            scores["control_window"] += 1
            reasons["control_window"].append("all target files are documentation or truth surfaces")
        if len(request.files) <= 4:
            scores["bounded_feature"] += 1
            reasons["bounded_feature"].append("requested file scope is bounded")

    if "RM-UI-005" in request.current_item:
        scores["bounded_feature"] += 2
        reasons["bounded_feature"].append("current item is implementation-heavy RM-UI-005")

    if not any(scores.values()):
        scores["bounded_feature"] = 1
        reasons["bounded_feature"].append("defaulted to bounded feature due to missing stronger signal")

    ordered = sorted(scores.items(), key=lambda item: (item[1], item[0]), reverse=True)
    selected_lane = ordered[0][0]
    competing = [
        LaneCandidate(lane=lane, score=score, reason="; ".join(reasons[lane]) or "no positive signal")
        for lane, score in ordered
    ]
    selected_reasons = reasons[selected_lane] or ["selected by default lane ordering"]

    return RouteDecision(
        selected_lane=selected_lane,
        rationale=selected_reasons,
        competing_lanes=competing,
        machine_route={
            "lane": selected_lane,
            "confidence": ordered[0][1],
            "current_item": request.current_item,
            "branch": request.branch or _current_branch(repo_root),
        },
    )


def build_aider_packet(
    request: RouteRequest,
    route: RouteDecision,
    context: ContextPressure,
) -> AiderRunPacket:
    lane = route.selected_lane
    aider_class = LANE_TO_AIDER_CLASS[lane]

    allowed_files = request.files or REQUIRED_ROUTE_FILES
    forbidden_files = [
        "secrets/**",
        "artifacts/**",
        "config/**",
        "systemd/**",
    ]
    if lane in {"control_window", "repo_audit"}:
        forbidden_files.extend(["**/*.pyc", "**/__pycache__/**"])

    preload_files: list[str] = []
    for rel in CANONICAL_TRUTH_SURFACES + REQUIRED_ROUTE_FILES:
        if rel not in preload_files:
            preload_files.append(rel)

    completion_criteria = [
        "required validations pass or are explicitly blocked with evidence",
        "required truth surfaces are updated when implementation changes status or behavior",
        "artifact visibility is refreshed for the current slice",
    ]
    if lane == "control_window":
        completion_criteria.extend([
            "patch success is separated from item completion",
            "blocker chain is surfaced with file-level evidence",
        ])
    if lane == "bounded_feature":
        completion_criteria.append("runnable first slice exists on disk")
    if lane == "repo_audit":
        completion_criteria.append("summary identifies real blockers without speculative fixes")

    payload = {
        "task": {
            "name": f"{request.current_item.lower()}-{lane}",
            "class": aider_class,
            "generated_by": "control_window",
        },
        "objective": request.objective,
        "target_files": [{"path": path, "action": "modify"} for path in allowed_files],
        "constraints": [
            f"selected lane: {lane}",
            "prefer deterministic routing and bounded scope",
            "do not bypass roadmap truth surfaces",
        ],
        "out_of_scope": [
            "broad unrelated roadmap work",
            "ungoverned architecture redesign",
        ],
        "acceptance_criteria": completion_criteria,
        "validation_commands": LANE_VALIDATIONS[lane],
        "limits": {
            "context_tokens_estimate": context.estimated_tokens,
            "context_limit_estimate": context.estimated_limit,
        },
        "escalate_if": LANE_STOP_CONDITIONS[lane],
    }

    packet_command = (
        f"python3 bin/aider_start_task.sh --name '{request.current_item.lower()}-{lane}' "
        f"--class {aider_class} --objective '{request.objective}'"
    )
    for path in allowed_files:
        packet_command += f" --file '{path}'"

    return AiderRunPacket(
        selected_lane=lane,
        aider_task_class=aider_class,
        objective=request.objective,
        bounded_scope=f"{request.current_item}::{lane}",
        allowed_files=allowed_files,
        forbidden_files=forbidden_files,
        preload_files=preload_files,
        drop_candidates=context.recommended_drop_candidates,
        validations_to_run=LANE_VALIDATIONS[lane],
        completion_criteria=completion_criteria,
        truth_surfaces_to_update=CANONICAL_TRUTH_SURFACES + [f"docs/roadmap/ITEMS/{request.current_item}.md"],
        stop_conditions=LANE_STOP_CONDITIONS[lane],
        packet_command=packet_command,
        packet_payload=payload,
    )


def build_openhands_plans(repo_root: Path, packet: AiderRunPacket) -> list[OpenHandsPlan]:
    _ = repo_root
    base_notes = [
        "OpenHands remains subordinate to roadmap truth, blocker truth, and completion truth.",
        "Prefer Docker-backed GUI mode when operator visibility matters more than CLI speed.",
    ]
    return [
        OpenHandsPlan(
            mode="cli",
            command=f"openhands --task {json.dumps(packet.objective)}",
            repo_mount_enabled=False,
            notes=base_notes + ["CLI mode is the lightest local execution path."],
        ),
        OpenHandsPlan(
            mode="web",
            command="openhands web --host 127.0.0.1 --port 12000",
            repo_mount_enabled=False,
            port=12000,
            notes=base_notes + ["Browser terminal mode; pair with the main control dashboard for truth panels."],
        ),
        OpenHandsPlan(
            mode="serve",
            command="openhands serve --mount-cwd",
            repo_mount_enabled=True,
            port=3000,
            notes=base_notes + ["Full local GUI server with current working directory mounted into /workspace."],
        ),
        OpenHandsPlan(
            mode="docker-serve",
            command="docker run --rm -p 3000:3000 -v ${PWD}:/workspace openhands/openhands:latest",
            repo_mount_enabled=True,
            port=3000,
            notes=base_notes + ["Fallback path when the OpenHands CLI is not installed locally."],
        ),
    ]


def _required_artifacts_for_lane(lane: LaneName) -> list[str]:
    artifacts = [
        "artifacts/intake/<task_id>/intake.json",
        "artifacts/intake/<task_id>/codex-escalation-packet.json",
    ]
    if lane in {"bounded_feature", "bugfix"}:
        artifacts.extend([
            "diff summary or changed-files evidence",
            "validation results for the bounded slice",
        ])
    artifacts.append("completion ladder state")
    return artifacts


def build_validation_state(repo_root: Path, route: RouteDecision) -> ValidationState:
    lane = route.selected_lane
    required_artifacts = _required_artifacts_for_lane(lane)

    emitted_artifacts: list[str] = []
    intake_root = repo_root / "artifacts" / "intake"
    if intake_root.exists():
        for path in sorted(intake_root.glob("*/intake.json")):
            emitted_artifacts.append(str(path.relative_to(repo_root)))
        for path in sorted(intake_root.glob("*/codex-escalation-packet.json")):
            emitted_artifacts.append(str(path.relative_to(repo_root)))

    required_validations = [
        {"command": cmd, "status": "pending", "reason": "not executed by snapshot builder"}
        for cmd in LANE_VALIDATIONS[lane]
    ]

    missing_evidence: list[str] = []
    if not emitted_artifacts:
        missing_evidence.append("no intake or escalation packet artifacts found under artifacts/intake/")
    if lane == "bounded_feature":
        missing_evidence.append("no validation receipt captured for runnable first slice yet")
    if lane == "control_window":
        missing_evidence.append("no completion-contract artifact captured yet")

    return ValidationState(
        required_validations=required_validations,
        required_artifacts=required_artifacts,
        emitted_artifacts=emitted_artifacts,
        missing_evidence=missing_evidence,
    )


def build_completion_ladder(route: RouteDecision, validations: ValidationState) -> CompletionLadder:
    pending_validations = [item for item in validations.required_validations if item["status"] != "pass"]
    missing = list(validations.missing_evidence)
    substep_complete = not missing
    bounded_slice_complete = substep_complete and not pending_validations
    item_complete = False
    blocker_chain_cleared = False
    objective_achieved = False
    reasons: list[str] = []
    if missing:
        reasons.extend(missing)
    if pending_validations:
        reasons.append("required validations are still pending or not captured")
    reasons.append("item completion requires explicit validation and truth-surface evidence")
    return CompletionLadder(
        substep_complete=substep_complete,
        bounded_slice_complete=bounded_slice_complete,
        item_complete=item_complete,
        blocker_chain_cleared=blocker_chain_cleared,
        objective_achieved=objective_achieved,
        reasons=reasons,
    )


def determine_next_target(repo_root: Path) -> tuple[NextTargetState, list[str]]:
    next_pull = _read_json(repo_root, "artifacts/planning/next_pull.json")
    if isinstance(next_pull, dict) and next_pull.get("selected_item"):
        selected_item = str(next_pull["selected_item"])
        competing_items = [str(item) for item in next_pull.get("competing_items", [])]
        return (
            NextTargetState(
                selected_item=selected_item,
                selected_reason="selected from artifacts/planning/next_pull.json",
                blocked_items=[],
                competing_items=competing_items,
            ),
            ["next_pull artifact present and treated as higher-priority derived planning output"],
        )

    status_sync = _read_text(repo_root, "docs/roadmap/ROADMAP_STATUS_SYNC.md")
    audit = _read_text(repo_root, "docs/roadmap/ACTIVE_ITEM_NORMALIZATION_AUDIT.md")
    status = _parse_status_sync(status_sync)
    normalization = _parse_normalization_audit(audit)
    normalized = set(normalization["normalized"])

    blocked_items: list[dict[str, str]] = []
    competing: list[str] = []

    for item_id in PREFERRED_ACTIVE_ORDER:
        if status.get(item_id) != "active":
            blocked_items.append({"item": item_id, "reason": f"status is {status.get(item_id, 'unknown')}, not active"})
            continue
        if item_id not in normalized:
            blocked_items.append({"item": item_id, "reason": "not listed as fully normalized active item"})
            continue
        competing.append(item_id)

    selected_item = competing[0] if competing else "none"
    selected_reason = (
        "highest remaining preferred active item that is also fully normalized for autonomous pull"
        if competing
        else "no normalized candidate found in the preferred active order"
    )

    return (
        NextTargetState(
            selected_item=selected_item,
            selected_reason=selected_reason,
            blocked_items=blocked_items,
            competing_items=competing[1:],
        ),
        [
            "ROADMAP_STATUS_SYNC governs visible status truth",
            "ACTIVE_ITEM_NORMALIZATION_AUDIT gates autonomous eligibility",
            "preferred order follows active focus bundle from summary roadmap docs",
        ],
    )


def build_blocker_chain(repo_root: Path, next_target: NextTargetState, validations: ValidationState) -> list[str]:
    blockers: list[str] = []
    blocker_registry = _read_json(repo_root, "artifacts/planning/blocker_registry.json")
    if isinstance(blocker_registry, dict):
        for item in blocker_registry.get("blockers", [])[:5]:
            blockers.append(str(item))
    for item in next_target.blocked_items:
        blockers.append(f"{item['item']}: {item['reason']}")
    blockers.extend(validations.missing_evidence)
    deduped: list[str] = []
    for blocker in blockers:
        if blocker not in deduped:
            deduped.append(blocker)
    return deduped[:10]


def build_dashboard_snapshot(
    repo_root: str | Path = ".",
    objective: str = "Implement RM-UI-005 first slice",
    files: list[str] | None = None,
    changed_files: list[str] | None = None,
    current_item: str = "RM-UI-005",
) -> DashboardSnapshot:
    root = Path(repo_root).resolve()
    request = RouteRequest(
        objective=objective,
        files=files or [],
        changed_files=changed_files or [],
        current_item=current_item,
        branch=_current_branch(root),
    )
    route = detect_route(request, root)
    context = estimate_context_pressure(root, request.files or REQUIRED_ROUTE_FILES, request.changed_files, route.selected_lane)
    validations = build_validation_state(root, route)
    completion = build_completion_ladder(route, validations)
    next_target, selection_notes = determine_next_target(root)
    blocker_chain = build_blocker_chain(root, next_target, validations)
    packet = build_aider_packet(request, route, context)
    openhands = build_openhands_plans(root, packet)
    truth_surfaces_read = CANONICAL_TRUTH_SURFACES + REQUIRED_ROUTE_FILES
    for rel in OPTIONAL_ARTIFACT_FILES:
        if (root / rel).exists():
            truth_surfaces_read.append(rel)
    truth_surfaces_read.extend(selection_notes)
    return DashboardSnapshot(
        current_objective=objective,
        current_item=current_item,
        branch=request.branch,
        blocker_chain=blocker_chain,
        next_target=next_target,
        context_pressure=context,
        validations=validations,
        completion_ladder=completion,
        route_decision=route,
        aider_packet=packet,
        openhands_paths=openhands,
        artifact_outputs=validations.emitted_artifacts,
        truth_surfaces_read=truth_surfaces_read,
    )


def render_dashboard_html(snapshot: DashboardSnapshot) -> str:
    def badge(value: str) -> str:
        return f"<span style='display:inline-block;padding:0.2rem 0.5rem;border:1px solid #ccc;border-radius:999px'>{html.escape(value)}</span>"

    def list_items(items: list[str]) -> str:
        if not items:
            return "<li>none</li>"
        return "".join(f"<li>{html.escape(item)}</li>" for item in items)

    validation_rows = "".join(
        "<tr>"
        f"<td>{html.escape(item['command'])}</td>"
        f"<td>{html.escape(item['status'])}</td>"
        f"<td>{html.escape(item['reason'])}</td>"
        "</tr>"
        for item in snapshot.validations.required_validations
    ) or "<tr><td colspan='3'>none</td></tr>"

    packet_json = html.escape(json.dumps(snapshot.aider_packet.packet_payload, indent=2))
    route_rows = "".join(
        "<tr>"
        f"<td>{html.escape(candidate.lane)}</td>"
        f"<td>{candidate.score}</td>"
        f"<td>{html.escape(candidate.reason)}</td>"
        "</tr>"
        for candidate in snapshot.route_decision.competing_lanes
    )

    openhands_rows = "".join(
        "<tr>"
        f"<td>{html.escape(plan.mode)}</td>"
        f"<td><code>{html.escape(plan.command)}</code></td>"
        f"<td>{'yes' if plan.repo_mount_enabled else 'no'}</td>"
        "</tr>"
        for plan in snapshot.openhands_paths
    )

    contributor_rows = "".join(
        "<tr>"
        f"<td>{html.escape(item['path'])}</td>"
        f"<td>{item['estimated_tokens']}</td>"
        f"<td>{'yes' if item['exists'] else 'no'}</td>"
        "</tr>"
        for item in snapshot.context_pressure.top_context_contributors
    ) or "<tr><td colspan='3'>none</td></tr>"

    blocked_rows = "".join(
        "<tr>"
        f"<td>{html.escape(item['item'])}</td>"
        f"<td>{html.escape(item['reason'])}</td>"
        "</tr>"
        for item in snapshot.next_target.blocked_items
    ) or "<tr><td colspan='2'>none</td></tr>"

    return f"""<!doctype html>
<html>
<head>
  <meta charset='utf-8' />
  <title>RM-UI-005 Control Window</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 0; padding: 1rem; background: #f7f7f7; }}
    h1, h2 {{ margin-top: 0; }}
    .grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; }}
    .card {{ background: white; border: 1px solid #ddd; border-radius: 8px; padding: 1rem; }}
    .wide {{ grid-column: span 2; }}
    table {{ width: 100%; border-collapse: collapse; }}
    td, th {{ text-align: left; border-bottom: 1px solid #eee; padding: 0.4rem; vertical-align: top; }}
    code, pre {{ background: #fafafa; border: 1px solid #eee; border-radius: 6px; }}
    pre {{ padding: 0.75rem; overflow-x: auto; }}
  </style>
</head>
<body>
  <h1>Local Execution Control Window</h1>
  <p>{badge(snapshot.current_item)} {badge(snapshot.route_decision.selected_lane)} {badge(snapshot.branch)}</p>
  <div class='grid'>
    <section class='card'>
      <h2>Objective</h2>
      <p>{html.escape(snapshot.current_objective)}</p>
      <ul>
        <li>Current item: {html.escape(snapshot.current_item)}</li>
        <li>Next governed target: {html.escape(snapshot.next_target.selected_item)}</li>
        <li>Next-target reason: {html.escape(snapshot.next_target.selected_reason)}</li>
      </ul>
    </section>
    <section class='card'>
      <h2>Completion Ladder</h2>
      <ul>
        <li>substep_complete: {str(snapshot.completion_ladder.substep_complete).lower()}</li>
        <li>bounded_slice_complete: {str(snapshot.completion_ladder.bounded_slice_complete).lower()}</li>
        <li>item_complete: {str(snapshot.completion_ladder.item_complete).lower()}</li>
        <li>blocker_chain_cleared: {str(snapshot.completion_ladder.blocker_chain_cleared).lower()}</li>
        <li>objective_achieved: {str(snapshot.completion_ladder.objective_achieved).lower()}</li>
      </ul>
      <ul>{list_items(snapshot.completion_ladder.reasons)}</ul>
    </section>
    <section class='card'>
      <h2>Blocker Chain</h2>
      <ul>{list_items(snapshot.blocker_chain)}</ul>
    </section>
    <section class='card'>
      <h2>Context / Token Pressure</h2>
      <ul>
        <li>estimated_tokens: {snapshot.context_pressure.estimated_tokens}</li>
        <li>estimated_limit: {snapshot.context_pressure.estimated_limit}</li>
        <li>overflow_risk: {html.escape(snapshot.context_pressure.overflow_risk)}</li>
      </ul>
      <p>recommended_drop_candidates:</p>
      <ul>{list_items(snapshot.context_pressure.recommended_drop_candidates)}</ul>
    </section>
    <section class='card wide'>
      <h2>Top Context Contributors</h2>
      <table>
        <thead><tr><th>path</th><th>estimated_tokens</th><th>exists</th></tr></thead>
        <tbody>{contributor_rows}</tbody>
      </table>
    </section>
    <section class='card wide'>
      <h2>Route Decision</h2>
      <table>
        <thead><tr><th>lane</th><th>score</th><th>reason</th></tr></thead>
        <tbody>{route_rows}</tbody>
      </table>
    </section>
    <section class='card wide'>
      <h2>Validation / Artifact State</h2>
      <table>
        <thead><tr><th>command</th><th>status</th><th>reason</th></tr></thead>
        <tbody>{validation_rows}</tbody>
      </table>
      <p>Required artifacts:</p>
      <ul>{list_items(snapshot.validations.required_artifacts)}</ul>
      <p>Emitted artifacts:</p>
      <ul>{list_items(snapshot.validations.emitted_artifacts)}</ul>
      <p>Missing evidence:</p>
      <ul>{list_items(snapshot.validations.missing_evidence)}</ul>
    </section>
    <section class='card wide'>
      <h2>Aider Run Packet</h2>
      <p><code>{html.escape(snapshot.aider_packet.packet_command)}</code></p>
      <pre>{packet_json}</pre>
    </section>
    <section class='card wide'>
      <h2>OpenHands Execution Paths</h2>
      <table>
        <thead><tr><th>mode</th><th>command</th><th>repo mount</th></tr></thead>
        <tbody>{openhands_rows}</tbody>
      </table>
    </section>
    <section class='card wide'>
      <h2>Blocked / Deferred Preferred Targets</h2>
      <table>
        <thead><tr><th>item</th><th>reason</th></tr></thead>
        <tbody>{blocked_rows}</tbody>
      </table>
    </section>
  </div>
</body>
</html>
"""
