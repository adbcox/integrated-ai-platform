#!/usr/bin/env python3
"""RECON-W2 Phase 2 extractor.

Deterministically generates:

- governance/inner_loop_contract.json
- governance/phase2_adoption_decision.json

The extractor statically walks ``framework/worker_runtime.py`` to identify
the inner-loop contract anchors:

- ``max_cycles`` source line
- ``setup_command`` and ``validate_command`` semantics
- ``repair_edits`` shape
- snapshot/restore trigger reasons
- failure classes emitted by ``_derive_failure_class``
- retryable failure classes (non-retryable complement)
- trace ``kind`` values emitted through the runtime

This packet records Phase 2 as ``adopted_partial`` and cannot set it to
``closed``.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Sequence

REPO_ROOT = Path(__file__).resolve().parent.parent
GOV_DIR = REPO_ROOT / "governance"
WORKER_RUNTIME = REPO_ROOT / "framework/worker_runtime.py"

SCHEMA_VERSION = 2
AUTHORITY_OWNER = "governance"
BASELINE_COMMIT = "53ae4d4f177b176a7bffaa63988f63fa0efa622c"

SUPERSEDES: Sequence[str] = (
    "config/promotion_manifest.json (legacy; frozen pending migration)",
    "docs/* narrative roadmaps (advisory only)",
)


def _run_git(args: Sequence[str]) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True).strip()


def _head_iso() -> str:
    return _run_git(["log", "-1", "--format=%cI", BASELINE_COMMIT])


def _read_runtime() -> str:
    return WORKER_RUNTIME.read_text(encoding="utf-8")


def _find_line(text: str, pattern: str) -> Dict[str, Any]:
    rx = re.compile(pattern)
    for idx, line in enumerate(text.splitlines(), start=1):
        if rx.search(line):
            return {"line": idx, "source": line.strip()}
    return {"line": None, "source": None}


def _extract_failure_classes(text: str) -> List[str]:
    # capture `return "..."` inside _derive_failure_class
    body_match = re.search(
        r"def _derive_failure_class\([^)]*\)[^:]*:\s*\n(.+?)(?=\n    def |\nclass |\Z)",
        text,
        flags=re.DOTALL,
    )
    if not body_match:
        return []
    body = body_match.group(1)
    classes = re.findall(r'return\s+"([^"]+)"', body)
    return sorted(set(classes))


def _extract_non_retryable(text: str) -> List[str]:
    body_match = re.search(
        r"def _is_retryable_failure[^:]*:\s*\n(.+?)(?=\n    def |\nclass |\Z)",
        text,
        flags=re.DOTALL,
    )
    if not body_match:
        return []
    body = body_match.group(1)
    return sorted(set(re.findall(r'"([a-z_]+)"', body)))


def _extract_snapshot_reasons(text: str) -> List[str]:
    reasons = re.findall(r'_restore_snapshot\([^)]*reason="([^"]+)"', text)
    return sorted(set(reasons))


def _extract_trace_kinds(text: str) -> List[str]:
    kinds = re.findall(r'"kind":\s*"([^"]+)"', text)
    return sorted(set(kinds))


def _build_contract() -> Dict[str, Any]:
    text = _read_runtime()
    failure_classes = _extract_failure_classes(text)
    non_retryable = _extract_non_retryable(text)
    retryable = sorted(set(failure_classes) - set(non_retryable) - {""})
    return {
        "schema_version": SCHEMA_VERSION,
        "authority_owner": AUTHORITY_OWNER,
        "generated_at": _head_iso(),
        "supersedes": list(SUPERSEDES),
        "baseline_commit": BASELINE_COMMIT,
        "max_cycles_source": _find_line(
            text, r'max_cycles\s*=\s*max\(1,\s*int\(config\.get\("max_cycles"\)'
        ),
        "setup_command_semantics": {
            "config_key": "setup_command",
            "failure_class_on_failure": "inner_loop_setup_failed",
            "snapshot_restore_reason": "setup_failed",
            "probe_line": _find_line(
                text, r'setup_command\s*=\s*str\(config\.get\("setup_command"'
            ),
        },
        "validate_command_semantics": {
            "config_key": "validate_command",
            "missing_failure_class": "inner_loop_config_error",
            "snapshot_restore_reason_on_missing": "missing_validate_command",
            "success_failure_class": "",
            "probe_line": _find_line(
                text, r'validate_command\s*=\s*str\(config\.get\("validate_command"'
            ),
        },
        "repair_edits_shape": {
            "config_key": "repair_edits",
            "expected_type": "list[dict]",
            "per_cycle_consumption": "one entry per cycle unless batch is allowed",
            "snapshot_restore_reason_on_exhaustion": "repairs_exhausted",
            "snapshot_restore_reason_on_repair_failure": "repair_failed",
            "probe_line": _find_line(
                text, r'repair_edits\s*=\s*config\.get\("repair_edits"\)'
            ),
        },
        "snapshot_restore_triggers": _extract_snapshot_reasons(text),
        "failure_classes": failure_classes,
        "retryable_failure_classes": retryable,
        "non_retryable_failure_classes": non_retryable,
        "trace_kinds_emitted": _extract_trace_kinds(text),
        "notes": (
            "Extraction is static; runtime-observed trace kinds may be a "
            "superset. The packet pins this to Phase 2 adopted_partial only."
        ),
    }


def _build_decision() -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "authority_owner": AUTHORITY_OWNER,
        "generated_at": _head_iso(),
        "supersedes": list(SUPERSEDES),
        "baseline_commit": BASELINE_COMMIT,
        "phase_id": 2,
        "decision": "adopted_partial",
        "code_anchors": [
            "framework/worker_runtime.py",
            "bin/framework_control_plane.py",
        ],
        "contract_ref": "governance/inner_loop_contract.json",
        "open_blockers": [
            "tactical families not reclassified onto the shared runtime",
            "real-capability evidence (measurement_session) not yet captured",
            "adoption coverage for multi_phase_/live_bridge_/ort_/pgs_ remains zero",
        ],
        "next_blocker_class": "capability_session",
        "as_of_commit": BASELINE_COMMIT,
        "ratified_by_adr": "governance/authority_adr_0005_phase2_partial_adoption.md",
    }


def build_all() -> Dict[str, Dict[str, Any]]:
    return {
        "inner_loop_contract.json": _build_contract(),
        "phase2_adoption_decision.json": _build_decision(),
    }


def _serialize(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def cmd_write() -> int:
    GOV_DIR.mkdir(parents=True, exist_ok=True)
    for name, payload in build_all().items():
        (GOV_DIR / name).write_text(_serialize(payload), encoding="utf-8")
    return 0


def cmd_check() -> int:
    diff = False
    for name, payload in build_all().items():
        expected = _serialize(payload)
        path = GOV_DIR / name
        if not path.exists():
            print(f"MISSING: {path}", file=sys.stderr)
            diff = True
            continue
        if path.read_text(encoding="utf-8") != expected:
            print(f"DIFF: {path}", file=sys.stderr)
            diff = True
    return 3 if diff else 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="RECON-W2 Phase 2 extractor")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--fail-on-diff", action="store_true")
    args = parser.parse_args(argv)
    if not (args.write or args.check or args.fail_on_diff):
        parser.error("one of --write, --check, or --fail-on-diff is required")
    if args.write:
        rc = cmd_write()
        if rc != 0:
            return rc
        if args.fail_on_diff or args.check:
            return cmd_check()
        return 0
    return cmd_check()


if __name__ == "__main__":
    sys.exit(main())
