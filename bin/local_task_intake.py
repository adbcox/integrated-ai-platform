#!/usr/bin/env python3
"""Local-first task intake with explicit mode routing and optional Codex escalation packet."""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MODE_RANK = {
    "tactical": 0,
    "codex-assist": 1,
    "codex-investigate": 2,
    "codex-failure": 3,
}


def parse_args() -> argparse.Namespace:
    script_dir = Path(__file__).resolve().parent
    base_dir = script_dir.parent
    default_rules = Path(os.environ.get("RULES_FILE", str(base_dir / "policies" / "local-routing-rules.json")))
    default_out_root = Path(os.environ.get("INTAKE_OUT_DIR", str(base_dir / "artifacts" / "intake")))

    parser = argparse.ArgumentParser(description="Local-first task intake and Codex escalation packetization.")
    parser.add_argument("--name", required=True, help="Task name")
    parser.add_argument("--goal", required=True, help="Task goal/problem statement")
    parser.add_argument("--class", dest="class_name", default="", help="Task class '<trigger> | <fix_pattern>'")
    parser.add_argument("--trigger", default="", help="Escalation trigger")
    parser.add_argument("--fix-pattern", default="", help="Fix/root-cause pattern")
    parser.add_argument("--constraints", action="append", default=[], help="Constraint text (repeatable)")
    parser.add_argument("--escalate", choices=["auto", "yes", "no"], default="auto", help="Escalation packet policy")
    parser.add_argument("--task-id", default="", help="Optional explicit task id")
    parser.add_argument("--rules-file", default=str(default_rules), help="Routing rules file")
    parser.add_argument("--out-dir", default=str(default_out_root), help="Intake artifacts root")
    parser.add_argument("--json", action="store_true", help="Print result JSON")
    parser.add_argument("--files", action="append", default=[], help="Target files for this request (repeatable)")
    parser.add_argument("--auto-route", action="store_true", help="Invoke aider_auto_route when classification is low-risk")
    return parser.parse_args()


def load_rules(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {
            "default_workflow_mode": "tactical",
            "class_overrides": [],
            "trigger_defaults": {},
            "operator_guidance": {
                "fallback_rule": "Rules missing; start tactical and escalate explicitly when blocked."
            },
        }
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_class_key(class_name: str, trigger: str, fix_pattern: str) -> str:
    if class_name.strip():
        return class_name.strip()
    if trigger.strip() and fix_pattern.strip():
        return f"{trigger.strip()} | {fix_pattern.strip()}"
    return ""


def select_mode(rules: dict[str, Any], class_key: str, trigger: str) -> tuple[str, str, str, str]:
    default_mode = str(rules.get("default_workflow_mode") or "tactical")

    for item in rules.get("class_overrides", []):
        if class_key and str(item.get("class")) == class_key:
            return (
                str(item.get("recommended_workflow_mode") or default_mode),
                "class_override",
                str(item.get("reason") or "matched class override"),
                str(item.get("heuristic") or ""),
            )

    trigger_defaults = rules.get("trigger_defaults", {})
    if trigger and trigger in trigger_defaults:
        td = trigger_defaults[trigger]
        return (
            str(td.get("recommended_workflow_mode") or default_mode),
            "trigger_default",
            f"matched trigger default: {trigger}",
            "",
        )

    return (default_mode, "global_default", "no specific class/trigger rule matched", "")


def should_escalate(mode: str, policy: str) -> bool:
    if policy == "yes":
        return True
    if policy == "no":
        return False
    return mode != "tactical"


def make_task_id(task_name: str, explicit_task_id: str) -> str:
    if explicit_task_id:
        return explicit_task_id
    slug = "".join(ch if ch.isalnum() or ch in "._-" else "-" for ch in task_name).strip("-")
    if not slug:
        slug = "task"
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"{ts}_{slug}"


def write_json(path: Path, obj: dict[str, Any]) -> None:
    path.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")


def write_packet_markdown(path: Path, packet: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# Codex Escalation Packet")
    lines.append("")
    lines.append(f"- task_id: {packet['task_id']}")
    lines.append(f"- timestamp_utc: {packet['timestamp_utc']}")
    lines.append(f"- repo: {packet['repo']}")
    lines.append(f"- branch: {packet['branch']}")
    lines.append(f"- recommended_workflow_mode: {packet['recommended_workflow_mode']}")
    lines.append(f"- routing_source: {packet['routing_source']}")
    lines.append(f"- routing_reason: {packet['routing_reason']}")
    lines.append("")
    lines.append("## Task")
    lines.append(f"- name: {packet['task_name']}")
    lines.append(f"- goal: {packet['goal']}")
    lines.append(f"- class: {packet['task_class'] or 'unspecified'}")
    lines.append(f"- trigger: {packet['trigger'] or 'unspecified'}")
    lines.append(f"- fix_pattern: {packet['fix_pattern'] or 'unspecified'}")
    lines.append("")
    lines.append("## Constraints")
    if packet["constraints"]:
        for c in packet["constraints"]:
            lines.append(f"- {c}")
    else:
        lines.append("- none specified")
    lines.append("")
    lines.append("## Operator Control")
    lines.append(f"- escalation_policy: {packet['escalation_policy']}")
    lines.append("- operator may override mode before execution")
    lines.append("")
    lines.append("## Suggested Commands")
    lines.append("```sh")
    lines.append(packet["suggested_local_command"])
    lines.append("# Candidate lane note: confirm metadata before handing off")
    lines.append("# Trace schema records the lane/stage metadata plus a success/failure classification so every win is logged for promotion evidence")
    lines.append(packet["suggested_handoff_command"])
    lines.append("```")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_heuristic_validation(path: Path, heuristic: str) -> None:
    success_signal = (
        "Escalation happens after exactly one local attempt and includes the full offline test context/logs."
    )
    lines = [
        "# Heuristic Validation",
        "",
        f"- heuristic: {heuristic}",
        f"- success_signal: {success_signal}",
        "- validation_status: pending",
        "",
        "## Notes",
        "- record when you escalated, what context was attached, and whether this prevented further wasted retries.",
        "- after finishing the task, update outcome notes / capture so the learning loop can evaluate it.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def current_branch(repo: Path) -> str:
    head = repo / ".git" / "HEAD"
    try:
        text = head.read_text(encoding="utf-8").strip()
    except OSError:
        return "unknown"
    if text.startswith("ref: refs/heads/"):
        return text.split("/")[-1]
    return "detached"


def main() -> int:
    args = parse_args()
    script_dir = Path(__file__).resolve().parent
    repo = script_dir.parent

    rules_path = Path(args.rules_file).resolve()
    out_root = Path(args.out_dir).resolve()
    rules = load_rules(rules_path)

    class_key = resolve_class_key(args.class_name, args.trigger, args.fix_pattern)
    mode, source, reason, heuristic_note = select_mode(rules, class_key, args.trigger.strip())

    if mode not in MODE_RANK:
        mode = "codex-assist"
        source = "rule_fallback"
        reason = "invalid mode in rule file; fell back to codex-assist"

    escalate = should_escalate(mode, args.escalate)

    constraints = args.constraints or []
    if not constraints:
        constraints = [
            "Prefer local-first execution when practical.",
            "Escalate deliberately for complex or high-ambiguity tasks.",
            "Keep changes machine-neutral and low-risk.",
        ]

    task_id = make_task_id(args.name, args.task_id)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    intake_dir = out_root / task_id
    intake_dir.mkdir(parents=True, exist_ok=True)

    auto_route_command = None
    if args.auto_route and args.files and mode == "tactical" and not args.force_class:
        try:
            from aider_lib import parse_file_spec
            from aider_auto_route import guess_class
            file_specs = [parse_file_spec(spec) for spec in args.files]
            task_class = guess_class(args.goal, file_specs)
            auto_route_command = (
                f"make aider-run AIDER_CLASS={task_class} AIDER_NAME=\"{args.name}\" "
                f"AIDER_OBJECTIVE=\"{args.goal}\" AIDER_FILES=\"{' '.join(args.files)}\""
            )
        except Exception as auto_exc:  # noqa: BLE001
            auto_route_command = f"# auto-route skipped: {auto_exc}"

    intake = {
        "task_id": task_id,
        "timestamp_utc": ts,
        "repo": str(repo),
        "branch": current_branch(repo),
        "task_name": args.name,
        "goal": args.goal,
        "task_class": class_key,
        "trigger": args.trigger.strip(),
        "fix_pattern": args.fix_pattern.strip(),
        "recommended_workflow_mode": mode,
        "routing_source": source,
        "routing_reason": reason,
        "applied_heuristic": heuristic_note,
        "escalation_policy": args.escalate,
        "escalation_selected": escalate,
        "constraints": constraints,
        "rules_file": str(rules_path),
        "auto_route_command": auto_route_command,
        "artifacts": {
            "intake_json": str(intake_dir / "intake.json"),
            "packet_json": str(intake_dir / "codex-escalation-packet.json"),
            "packet_md": str(intake_dir / "codex-escalation-packet.md"),
        },
    }

    write_json(intake_dir / "intake.json", intake)

    if heuristic_note:
        write_heuristic_validation(intake_dir / "heuristic-validation.md", heuristic_note)

    packet_written = False
    if escalate:
        packet = {
            "packet_version": "1",
            "task_id": task_id,
            "timestamp_utc": ts,
            "repo": str(repo),
            "branch": intake["branch"],
            "task_name": args.name,
            "goal": args.goal,
            "task_class": class_key,
            "trigger": args.trigger.strip(),
            "fix_pattern": args.fix_pattern.strip(),
            "recommended_workflow_mode": mode,
            "routing_source": source,
            "routing_reason": reason,
            "escalation_policy": args.escalate,
            "constraints": constraints,
            "applied_heuristic": heuristic_note,
            "suggested_local_command": f"WORKFLOW_MODE={mode} ./bin/aider_loop.sh --name '{args.name}' --goal '{args.goal}'",
            "suggested_handoff_command": f"./bin/aider_handoff.sh --task-file tmp/<task-brief>.md --name '{args.name}'",
            "learning_tags": {
                "intent": "local-first-front-door",
                "capture_expected": True,
                "evaluation_expected": True,
            },
        }
        write_json(intake_dir / "codex-escalation-packet.json", packet)
        write_packet_markdown(intake_dir / "codex-escalation-packet.md", packet)
        packet_written = True

    result = {
        "task_id": task_id,
        "recommended_workflow_mode": mode,
        "routing_source": source,
        "routing_reason": reason,
        "applied_heuristic": heuristic_note,
        "escalation_selected": escalate,
        "intake_dir": str(intake_dir),
        "packet_written": packet_written,
    }

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"task_id: {task_id}")
        print(f"recommended_mode: {mode}")
        print(f"routing_source: {source}")
        print(f"routing_reason: {reason}")
        if heuristic_note:
            print(f"applied_heuristic: {heuristic_note}")
        print(f"escalation_selected: {str(escalate).lower()}")
        print(f"intake_artifact: {intake_dir / 'intake.json'}")
        if packet_written:
            print(f"escalation_packet_json: {intake_dir / 'codex-escalation-packet.json'}")
            print(f"escalation_packet_md: {intake_dir / 'codex-escalation-packet.md'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
