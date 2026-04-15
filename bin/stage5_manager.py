#!/usr/bin/env python3
"""Stage-5 manager: bounded multi-file literal orchestrator."""

from __future__ import annotations  # stage6-grouped

import argparse  # stage7-op  # stage6-rag4-v4b
import json  # stage6-linkscore-v2
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from promotion import MANIFEST_PATH, load_manifest, resolve_versions_for_lane
from promotion.failure_memory import assess_target_risk, message_has_target_ref
STAGE4_MANAGER = REPO_ROOT / "bin" / "stage4_manager.py"
STAGE_RAG3 = REPO_ROOT / "bin" / "stage_rag3_plan_probe.py"
TRACE_DIR = REPO_ROOT / "artifacts" / "stage5_manager"
TRACE_FILE = TRACE_DIR / "traces.jsonl"
DEFAULT_MAX_OPS = 2  # Manager-4 batches stay within two entries until Stage-5 saturation completes.
DEFAULT_MAX_TOTAL_LINES = 20
DEFAULT_MANIFEST_PATH = MANIFEST_PATH
PROMOTION_ENV_KEYS = {
    "promotion_lane": "PROMOTION_LANE",
    "promotion_lane_status": "PROMOTION_LANE_STATUS",
    "promotion_lane_label": "PROMOTION_LANE_LABEL",
    "promotion_lane_reason": "PROMOTION_LANE_REASON",
    "promotion_stage_version": "PROMOTION_STAGE_VERSION",
    "promotion_stage_name": "PROMOTION_STAGE_NAME",
    "promotion_manager_version": "PROMOTION_MANAGER_VERSION",
    "promotion_rag_version": "PROMOTION_RAG_VERSION",
    "promotion_manifest_version": "PROMOTION_MANIFEST_VERSION",
    "promotion_manifest_path": "PROMOTION_MANIFEST_PATH",
}


class Stage5Error(SystemExit):
    pass


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    kwargs.setdefault("check", True)
    return subprocess.run(cmd, **kwargs)


def ensure_clean_tree() -> None:
    status = run(["git", "status", "--porcelain"], capture_output=True, text=True)
    if status.stdout.strip():
        raise Stage5Error("Stage-5 manager requires a clean working tree")


def load_candidate_allowed_targets(manifest_path: Path) -> list[str]:
    manifest = load_manifest(manifest_path)
    lane_cfg = resolve_versions_for_lane(manifest.data, "candidate")["lane"]
    return list(lane_cfg.get("allowed_targets", []))


def enforce_allowed_targets(entries: list[dict[str, Any]], allowed: list[str]) -> None:
    if not allowed:
        return
    for entry in entries:
        target = entry["target"]
        if not any(target.startswith(prefix) for prefix in allowed):
            raise Stage5Error(
                f"Target '{target}' is not allowed for Stage-5 candidate lane. "
                f"Allowed prefixes: {allowed}"
            )


def load_batch(path: Path) -> list[dict[str, Any]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise Stage5Error(f"batch file is not valid JSON: {exc}") from exc
    if not isinstance(data, list) or not data:
        raise Stage5Error("batch file must contain a non-empty JSON array")
    entries: list[dict[str, Any]] = []
    for idx, entry in enumerate(data, start=1):
        if not isinstance(entry, dict):
            raise Stage5Error(f"batch entry #{idx} is not an object")
        required = {"query", "target", "message"}
        if not required.issubset(entry):
            missing = required.difference(entry)
            raise Stage5Error(f"batch entry #{idx} missing keys: {', '.join(sorted(missing))}")
        entries.append(entry)
    return entries


def ensure_message_anchor(message: str, target: str) -> str:
    if message_has_target_ref(message, target):
        return message
    return f"{target}:: {message}"


def log_trace(entry: dict) -> None:
    for dest, env_key in PROMOTION_ENV_KEYS.items():
        entry[dest] = os.environ.get(env_key)
    TRACE_DIR.mkdir(parents=True, exist_ok=True)
    with TRACE_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def git_head() -> str:
    proc = run(["git", "rev-parse", "HEAD"], capture_output=True, text=True)
    return proc.stdout.strip()


def restore_head(ref: str) -> None:
    run(["git", "reset", "--hard", ref])


def diff_stats(paths: list[str]) -> tuple[int, int]:
    proc = run(["git", "diff", "--numstat", "--"] + paths, capture_output=True, text=True)
    added = deleted = 0
    for line in proc.stdout.splitlines():
        parts = line.split()
        if len(parts) < 3:
            continue
        if parts[2] not in paths:
            continue
        try:
            added += int(parts[0])
            deleted += int(parts[1])
        except ValueError:
            continue
    return added, deleted


def _safe_check(cmd: list[str]) -> tuple[bool, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    output = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
    return proc.returncode == 0, output.strip()[:400]


def _safe_check_with_timeout(cmd: list[str], *, timeout_seconds: int) -> tuple[bool, str]:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=max(1, timeout_seconds))
    except subprocess.TimeoutExpired as exc:
        output = (exc.stdout or "") + ("\n" + exc.stderr if exc.stderr else "")
        detail = f"timeout_after_{timeout_seconds}s"
        merged = f"{detail}\n{output}".strip()
        return False, merged[:400]
    output = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
    return proc.returncode == 0, output.strip()[:400]


def _file_looks_like_python_entrypoint(path: Path) -> bool:
    try:
        contents = path.read_text(encoding="utf-8")
    except OSError:
        return False
    return "argparse.ArgumentParser" in contents and "if __name__ == \"__main__\"" in contents


def _run_shell_common_smoke() -> tuple[bool, str]:
    common_sh = REPO_ROOT / "shell" / "common.sh"
    if not common_sh.exists():
        return False, "shell/common.sh_missing"
    checks = [
        ["sh", "-c", '. "$1"; extract_session_id "{\\"session_id\\":\\"abc-123\\"}"', "sh", str(common_sh)],
        ["sh", "-c", '. "$1"; extract_session_id "Using session: abc-123"', "sh", str(common_sh)],
        ["sh", "-c", '. "$1"; require_exec sh', "sh", str(common_sh)],
    ]
    for cmd in checks:
        ok, detail = _safe_check(cmd)
        if not ok:
            return False, detail
    return True, "ok"


def _status_block(*, total: int, passed: int, available: bool = True) -> dict[str, Any]:
    return {
        "available": available,
        "total": max(0, int(total)),
        "passed": max(0, int(min(passed, total if total > 0 else passed))),
        "failed": max(0, int(total) - int(min(passed, total if total > 0 else passed))),
    }


def collect_code_outcomes(*, modified_files: list[str]) -> dict[str, Any]:
    python_total = 0
    python_passed = 0
    shell_total = 0
    shell_passed = 0
    python_entrypoint_total = 0
    python_entrypoint_passed = 0
    shell_bash_total = 0
    shell_bash_passed = 0
    shell_common_smoke_total = 0
    shell_common_smoke_passed = 0
    per_file: list[dict[str, Any]] = []
    common_shell_changed = False
    for rel_path in modified_files:
        row: dict[str, Any] = {"path": rel_path}
        abs_path = REPO_ROOT / rel_path
        if rel_path.endswith(".py"):
            python_total += 1
            ok, detail = _safe_check([sys.executable, "-m", "py_compile", str(abs_path)])
            if ok:
                python_passed += 1
            row["python_compile"] = {"passed": ok, "detail": detail}
            if rel_path.startswith("bin/") and _file_looks_like_python_entrypoint(abs_path):
                python_entrypoint_total += 1
                help_ok, help_detail = _safe_check_with_timeout(
                    [sys.executable, str(abs_path), "--help"],
                    timeout_seconds=12,
                )
                if help_ok:
                    python_entrypoint_passed += 1
                row["python_entrypoint_help"] = {"passed": help_ok, "detail": help_detail}
        if rel_path.endswith(".sh"):
            common_shell_changed = common_shell_changed or rel_path == "shell/common.sh"
            shell_total += 1
            ok, detail = _safe_check(["sh", "-n", str(abs_path)])
            if ok:
                shell_passed += 1
            row["shell_syntax"] = {"passed": ok, "detail": detail}
            try:
                first_line = abs_path.read_text(encoding="utf-8").splitlines()[0]
            except (OSError, IndexError):
                first_line = ""
            if "bash" in first_line and shutil.which("bash"):
                shell_bash_total += 1
                bash_ok, bash_detail = _safe_check(["bash", "-n", str(abs_path)])
                if bash_ok:
                    shell_bash_passed += 1
                row["shell_bash_syntax"] = {"passed": bash_ok, "detail": bash_detail}
        per_file.append(row)

    if common_shell_changed:
        shell_common_smoke_total = 1
        smoke_ok, smoke_detail = _run_shell_common_smoke()
        if smoke_ok:
            shell_common_smoke_passed = 1
    else:
        smoke_ok = None
        smoke_detail = "not_applicable"

    committed = run(["git", "show", "--name-only", "--pretty=format:", "HEAD"], capture_output=True, text=True)
    committed_files = sorted({line.strip() for line in committed.stdout.splitlines() if line.strip()})
    expected_files = sorted({path for path in modified_files if path})
    diff_integrity_ok = committed_files == expected_files

    checks_total = (
        python_total
        + python_entrypoint_total
        + shell_total
        + shell_bash_total
        + shell_common_smoke_total
    )
    checks_passed = (
        python_passed
        + python_entrypoint_passed
        + shell_passed
        + shell_bash_passed
        + shell_common_smoke_passed
    )
    score = round((checks_passed / checks_total), 3) if checks_total else 0.0
    return {
        "summary": {
            "quality_score": score,
            "checks_total": checks_total,
            "checks_passed": checks_passed,
            "diff_integrity_ok": diff_integrity_ok,
            "files_touched": len(expected_files),
        },
        "python_compile": {
            "available": True,
            "total": python_total,
            "passed": python_passed,
            "failed": max(0, python_total - python_passed),
        },
        "python_entrypoint_help": _status_block(total=python_entrypoint_total, passed=python_entrypoint_passed),
        "shell_syntax": {
            "available": True,
            "total": shell_total,
            "passed": shell_passed,
            "failed": max(0, shell_total - shell_passed),
        },
        "shell_bash_syntax": _status_block(
            total=shell_bash_total,
            passed=shell_bash_passed,
            available=bool(shutil.which("bash")),
        ),
        "shell_common_smoke": {
            **_status_block(total=shell_common_smoke_total, passed=shell_common_smoke_passed),
            "detail": smoke_detail,
            "passed_bool": smoke_ok,
        },
        "test": _status_block(total=shell_common_smoke_total, passed=shell_common_smoke_passed),
        "lint": {"available": False, "status": "not_run"},
        "typecheck": {"available": False, "status": "not_run"},
        "build": _status_block(total=python_entrypoint_total, passed=python_entrypoint_passed),
        "committed_files": committed_files,
        "expected_files": expected_files,
        "per_file": per_file,
    }


LITERAL_REPLACE_RE = re.compile(r"replace exact text '(.+?)' with '(.+?)'", re.DOTALL)


def _extract_message_literals(message: str) -> tuple[str | None, str | None]:
    match = LITERAL_REPLACE_RE.search(message)
    if not match:
        return None, None
    return match.group(1), match.group(2)


def _apply_literal_replace_direct(*, target: str, message: str) -> tuple[bool, str]:
    old_literal, new_literal = _extract_message_literals(message)
    if not old_literal or new_literal is None:
        return False, "literal_contract_missing"
    target_path = REPO_ROOT / target
    try:
        before = target_path.read_text(encoding="utf-8")
    except OSError:
        return False, "target_unreadable"
    if old_literal not in before:
        return False, "literal_old_not_found"
    after = before.replace(old_literal, new_literal, 1)
    if after == before:
        return False, "literal_noop"
    target_path.write_text(after, encoding="utf-8")
    return True, "literal_direct_applied"


def stage5_manager(args: argparse.Namespace) -> None:
    ensure_clean_tree()
    batch_path = Path(args.batch_file).resolve()
    entries = load_batch(batch_path)
    manifest_path = Path(args.manifest).resolve()
    allowed_targets = load_candidate_allowed_targets(manifest_path)
    enforce_allowed_targets(entries, allowed_targets)
    if len(entries) > args.max_ops:
        raise Stage5Error(f"Stage-5 manager currently supports at most {args.max_ops} operations per batch")

    lane = os.environ.get("PROMOTION_LANE", "candidate")
    manifest_version_raw = os.environ.get("PROMOTION_MANIFEST_VERSION")
    manifest_version = int(manifest_version_raw) if manifest_version_raw and manifest_version_raw.isdigit() else None
    filtered_entries: list[dict[str, Any]] = []
    memory_findings: list[dict[str, Any]] = []
    for entry in entries:
        target = str(entry["target"])
        message = str(entry["message"] or "")
        decision = assess_target_risk(
            lane=lane,
            target=target,
            message=message,
            manifest_version=manifest_version,
            retry_class="none",
        )
        entry["message"] = ensure_message_anchor(message, target)
        finding = {
            "target": target,
            "reason": decision.reason,
            "failures_by_class": decision.failures_by_class,
            "successes": decision.successes,
            "forced_anchor": bool(entry["message"] != message),
            "rerouted_manual": decision.should_reroute_manual,
        }
        memory_findings.append(finding)
        if decision.should_reroute_manual and lane == "candidate":
            # Keep candidate lanes away from shell-risk classes; let manual/Codex handle it.
            continue
        filtered_entries.append(entry)
    entries = filtered_entries
    if not entries:
        raise Stage5Error("all batch entries were blocked by failure-memory preflight; reroute to manual lane")

    start_head = git_head()
    job_id = datetime.now(UTC).strftime("stage5-%Y%m%d-%H%M%S")
    modified_files: list[str] = []
    operation_details: list[dict[str, Any]] = []
    plan_ids: list[str] = []

    patch_records: list[tuple[str, Path]] = []
    total_added = 0
    total_deleted = 0
    commit_hash: str | None = None
    code_outcomes: dict[str, Any] = {
        "summary": {"quality_score": 0.0, "checks_total": 0, "checks_passed": 0, "diff_integrity_ok": False}
    }

    try:
        for idx, entry in enumerate(entries, start=1):
            target = entry["target"]
            message = entry["message"].replace("\\n", "\n")
            query = entry["query"]
            notes = entry.get("notes", "")
            stage4_notes = notes or f"stage5 op {idx}"
            lines = entry.get("lines", "auto")

            plan_id = f"{job_id}-op{idx}"
            plan_ids.append(plan_id)
            rag_cmd = [
                sys.executable,
                str(STAGE_RAG3),
                "--stage",
                "stage5",
                "--plan-id",
                plan_id,
                "--top",
                str(args.rag_top),
                "--selected-path",
                target,
                "--selected-lines",
                str(lines),
                "--notes",
                stage4_notes,
                "--",
            ]
            rag_cmd.extend(query.split())
            run(rag_cmd)

            stage4_cmd = [
                sys.executable,
                str(STAGE4_MANAGER),
                "--query",
                query,
                "--target",
                target,
                "--message",
                message,
                "--commit-msg",
                f"stage5-op{idx}",
                "--lines",
                str(lines),
                "--notes",
                stage4_notes,
                "--no-commit",
                "--allow-literal-diff",
            ]
            if entry.get("min_lines"):
                stage4_cmd.extend(["--min-lines", str(entry["min_lines"])])
            if entry.get("top"):
                stage4_cmd.extend(["--top", str(entry["top"])])
            if entry.get("window"):
                stage4_cmd.extend(["--window", str(entry["window"])])
            if entry.get("max_total_lines"):
                stage4_cmd.extend(["--max-total-lines", str(entry["max_total_lines"])])
            direct_ok, direct_reason = _apply_literal_replace_direct(target=target, message=message)
            if not direct_ok:
                run(stage4_cmd)
            if target not in modified_files:
                modified_files.append(target)

            entry_added, entry_deleted = diff_stats([target])
            operation_details.append(
                {
                    "plan_id": plan_id,
                    "target": target,
                    "query": query,
                    "lines": lines,
                    "notes": stage4_notes,
                    "execution_mode": "literal_direct" if direct_ok else "stage4_manager",
                    "execution_reason": direct_reason,
                    "diff_added": entry_added,
                    "diff_deleted": entry_deleted,
                }
            )

            diff_proc = run(["git", "diff", "--", target], capture_output=True, text=True)
            if not diff_proc.stdout.strip():
                raise Stage5Error(f"Stage-4 operation on {target} produced no diff")
            patch_fd, patch_path_str = tempfile.mkstemp(prefix=f"stage5_{idx}_", suffix=".patch")
            os.close(patch_fd)
            patch_path = Path(patch_path_str)
            patch_path.write_text(diff_proc.stdout, encoding="utf-8")
            patch_records.append((target, patch_path))
            run(["git", "checkout", "--", target])
            run(["git", "restore", "--staged", target])

        total_added = sum(detail["diff_added"] for detail in operation_details)
        total_deleted = sum(detail["diff_deleted"] for detail in operation_details)
        if total_added + total_deleted > args.max_total_lines:
            raise Stage5Error(
                f"Stage-5 diff exceeded limit ({total_added + total_deleted}>{args.max_total_lines}); revert and retry with smaller scope"
            )

        for target, patch_path in patch_records:
            run(["git", "apply", str(patch_path)])
        run(["git", "add"] + modified_files)
        run(["git", "commit", "-m", args.commit_msg])
        commit_hash = git_head()
        code_outcomes = collect_code_outcomes(modified_files=modified_files)
    except Exception as exc:
        restore_head(start_head)
        log_trace(
            {
                "timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
                "job_id": job_id,
                "batch_file": str(batch_path),
                "operations": len(entries),
                "targets": modified_files,
                "plan_ids": plan_ids,
                "commit_msg": args.commit_msg,
                "max_ops": args.max_ops,
                "max_total_lines": args.max_total_lines,
                "total_added": total_added,
                "total_deleted": total_deleted,
                "operation_details": operation_details,
                "status": "failure",
                "error": str(exc),
                "rollback_to": start_head,
                "commit_hash": None,
                "end_head": git_head(),
                "failure_memory_findings": memory_findings,
                "code_outcomes": {
                    "summary": {
                        "quality_score": 0.0,
                        "checks_total": 0,
                        "checks_passed": 0,
                        "diff_integrity_ok": False,
                    },
                    "error": "stage5_failed_before_quality_checks",
                },
            }
        )
        if isinstance(exc, Stage5Error):
            raise
        raise Stage5Error(str(exc)) from exc
    finally:
        for _, patch_path in patch_records:
            try:
                patch_path.unlink()
            except FileNotFoundError:
                pass

    log_trace(
        {
            "timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
            "job_id": job_id,
            "batch_file": str(batch_path),
            "operations": len(entries),
            "targets": modified_files,
            "plan_ids": plan_ids,
            "commit_msg": args.commit_msg,
            "max_ops": args.max_ops,
            "max_total_lines": args.max_total_lines,
            "total_added": total_added,
            "total_deleted": total_deleted,
            "operation_details": operation_details,
            "status": "success",
            "start_head": start_head,
            "end_head": git_head(),
            "rollback_to": None,
            "commit_hash": commit_hash,
            "failure_memory_findings": memory_findings,
            "code_outcomes": code_outcomes,
        }
    )
    target_summary = ", ".join(modified_files)
    print(f"[stage5_manager] completed batch {job_id}; committed {args.commit_msg} (targets={target_summary})")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage-5 bounded multi-file literal manager")
    parser.add_argument("--batch-file", required=True, help="JSON file describing up to two literal operations")
    parser.add_argument("--commit-msg", required=True, help="Commit message for the combined change")
    parser.add_argument("--max-ops", type=int, default=DEFAULT_MAX_OPS)
    parser.add_argument("--max-total-lines", type=int, default=DEFAULT_MAX_TOTAL_LINES)
    parser.add_argument("--rag-top", type=int, default=6)
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST_PATH), help="Promotion manifest path for allowed targets")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        stage5_manager(args)
    except Stage5Error as exc:
        print(f"[stage5_manager] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
