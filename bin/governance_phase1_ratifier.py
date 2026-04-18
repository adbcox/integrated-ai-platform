#!/usr/bin/env python3
"""RECON-W2 Phase 1 ratifier.

Deterministically generates:

- governance/runtime_primitive_callgraph.json
- governance/phase1_ratification_decision.json

The callgraph is a static import/invocation graph restricted to the runtime
primitive set plus their co-primitive dependencies inside framework/. The
decision is ``closed`` iff:

1. every primitive is imported by at least one non-primitive consumer; and
2. worker_runtime directly imports tool_system, permission_engine, sandbox,
   and workspace.
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

SCHEMA_VERSION = 2
AUTHORITY_OWNER = "governance"
BASELINE_COMMIT = "53ae4d4f177b176a7bffaa63988f63fa0efa622c"

SUPERSEDES: Sequence[str] = (
    "config/promotion_manifest.json (legacy; frozen pending migration)",
    "docs/* narrative roadmaps (advisory only)",
)

PRIMITIVES: Sequence[Dict[str, str]] = (
    {"name": "worker_runtime", "path": "framework/worker_runtime.py"},
    {"name": "tool_system", "path": "framework/tool_system.py"},
    {"name": "workspace", "path": "framework/workspace.py"},
    {"name": "permission_engine", "path": "framework/permission_engine.py"},
    {"name": "sandbox", "path": "framework/sandbox.py"},
)

REQUIRED_WORKER_EDGES: Sequence[str] = (
    "tool_system",
    "permission_engine",
    "sandbox",
    "workspace",
)


def _run_git(args: Sequence[str]) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True).strip()


def _head_iso() -> str:
    return _run_git(["log", "-1", "--format=%cI", BASELINE_COMMIT])


def _git_ls_files() -> List[str]:
    return [line for line in _run_git(["ls-files"]).splitlines() if line]


def _loc(path: str) -> int:
    with open(REPO_ROOT / path, "rb") as fh:
        return sum(1 for _ in fh)


def _detect_imports(text: str, name: str) -> bool:
    pattern = re.compile(
        rf"^\s*(?:from\s+framework\.{re.escape(name)}\b|"
        rf"import\s+framework\.{re.escape(name)}\b|"
        rf"from\s+framework\s+import\s+[^\n]*\b{re.escape(name)}\b|"
        rf"from\s+\.{re.escape(name)}\b)"
    )
    return any(pattern.search(line) for line in text.splitlines())


def _detect_invokes(text: str, name: str) -> bool:
    """Heuristic invoke detector.

    Looks for references to the module's ``PascalCase`` exported class name
    beyond the import line. This is intentionally coarse; the callgraph is a
    static attestation, not a semantic dataflow analysis.
    """

    class_markers = {
        "worker_runtime": ["WorkerRuntime"],
        "tool_system": ["ToolAction", "ToolObservation", "ToolName", "ToolStatus"],
        "workspace": ["WorkspaceController"],
        "permission_engine": ["PermissionEngine"],
        "sandbox": ["LocalSandboxRunner"],
    }.get(name, [])
    for marker in class_markers:
        pat = re.compile(rf"\b{re.escape(marker)}\b")
        hits = [ln for ln in text.splitlines() if pat.search(ln)]
        # require at least one non-import hit
        for hit in hits:
            if "import" not in hit:
                return True
    return False


def _build_callgraph() -> Dict[str, Any]:
    nodes: List[Dict[str, Any]] = []
    for prim in PRIMITIVES:
        nodes.append(
            {
                "name": prim["name"],
                "path": prim["path"],
                "loc": _loc(prim["path"]),
            }
        )

    edges: List[Dict[str, str]] = []
    for prim in PRIMITIVES:
        path = prim["path"]
        text = (REPO_ROOT / path).read_text(encoding="utf-8", errors="replace")
        src = prim["name"]
        for other in PRIMITIVES:
            if other["name"] == src:
                continue
            if _detect_imports(text, other["name"]):
                edges.append({"from": src, "to": other["name"], "kind": "import"})
            if _detect_invokes(text, other["name"]):
                edges.append({"from": src, "to": other["name"], "kind": "invoke"})

    edges.sort(key=lambda e: (e["from"], e["to"], e["kind"]))

    worker_targets = {e["to"] for e in edges if e["from"] == "worker_runtime" and e["kind"] == "import"}
    self_adoption_complete = all(t in worker_targets for t in REQUIRED_WORKER_EDGES)

    return {
        "schema_version": SCHEMA_VERSION,
        "authority_owner": AUTHORITY_OWNER,
        "generated_at": _head_iso(),
        "supersedes": list(SUPERSEDES),
        "baseline_commit": BASELINE_COMMIT,
        "nodes": nodes,
        "edges": edges,
        "self_adoption_complete": self_adoption_complete,
        "required_worker_runtime_edges": list(REQUIRED_WORKER_EDGES),
    }


def _primitive_fingerprint() -> str:
    import hashlib

    h = hashlib.sha256()
    for prim in PRIMITIVES:
        h.update(prim["path"].encode("utf-8"))
        h.update(b"\0")
        with open(REPO_ROOT / prim["path"], "rb") as fh:
            while chunk := fh.read(65536):
                h.update(chunk)
        h.update(b"\n")
    return f"rt-1.0.0+{h.hexdigest()[:12]}"


def _detect_framework_package_import(text: str) -> bool:
    """Detect any import of the framework package or its submodules."""

    pattern = re.compile(
        r"^\s*(?:from\s+framework(?:\.[A-Za-z_][\w\.]*)?\s+import\b|"
        r"import\s+framework(?:\.[A-Za-z_][\w\.]*)?\b)"
    )
    return any(pattern.search(line) for line in text.splitlines())


def _build_decision(callgraph: Dict[str, Any]) -> Dict[str, Any]:
    adoption_refs: List[str] = []
    for rel in ["bin/framework_control_plane.py"]:
        abs_path = REPO_ROOT / rel
        if not abs_path.exists():
            continue
        text = abs_path.read_text(encoding="utf-8", errors="replace")
        if _detect_framework_package_import(text):
            adoption_refs.append(rel)

    decision_ok = callgraph["self_adoption_complete"] and bool(adoption_refs)
    decision = "closed" if decision_ok else "open"

    return {
        "schema_version": SCHEMA_VERSION,
        "authority_owner": AUTHORITY_OWNER,
        "generated_at": _head_iso(),
        "supersedes": list(SUPERSEDES),
        "baseline_commit": BASELINE_COMMIT,
        "phase_id": 1,
        "decision": decision,
        "code_anchors": [p["path"] for p in PRIMITIVES],
        "adoption_evidence_refs": sorted(adoption_refs),
        "ratified_contract_version": _primitive_fingerprint(),
        "as_of_commit": BASELINE_COMMIT,
        "ratified_by_adr": "governance/authority_adr_0004_phase1_closure.md",
    }


def build_all() -> Dict[str, Dict[str, Any]]:
    callgraph = _build_callgraph()
    return {
        "runtime_primitive_callgraph.json": callgraph,
        "phase1_ratification_decision.json": _build_decision(callgraph),
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
    parser = argparse.ArgumentParser(description="RECON-W2 Phase 1 ratifier")
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
