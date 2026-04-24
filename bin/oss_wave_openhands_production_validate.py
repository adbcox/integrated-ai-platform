#!/usr/bin/env python3
"""Production validation for canonical OpenHands deployment."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
import glob
import re


REPO_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_PATH = REPO_ROOT / "artifacts" / "oss_wave" / "openhands_production_validation.json"
HOST_URL = "http://127.0.0.1:3000"


def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        check=check,
        text=True,
        capture_output=True,
    )


def cmd_ok(cmd: list[str]) -> tuple[bool, str]:
    proc = run(cmd, check=False)
    out = (proc.stdout + proc.stderr).strip()
    return proc.returncode == 0, out


def detect_lan_url() -> str | None:
    env_host = os.environ.get("OPENHANDS_LAN_HOST", "").strip()
    if env_host:
        return f"http://{env_host}:3000"
    ok, out = cmd_ok(["ipconfig", "getifaddr", "en0"])
    if ok and out:
        return f"http://{out}:3000"
    return None


def determine_canonical_owner() -> dict[str, object]:
    item_files = sorted((REPO_ROOT / "docs" / "roadmap" / "ITEMS").glob("RM-*.md"))
    explicit_owner_candidates: list[str] = []
    evidence: list[str] = []

    owner_patterns = (
        "company knowledge base branch",
        "knowledge base branch owner",
        "owns the company knowledge base branch",
    )

    for path in item_files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        low = text.lower()
        if any(pat in low for pat in owner_patterns):
            explicit_owner_candidates.append(path.stem)
            evidence.append(str(path.relative_to(REPO_ROOT)))

    if len(explicit_owner_candidates) == 1:
        return {
            "owner": explicit_owner_candidates[0],
            "source_type": "canonical_item",
            "evidence_files": evidence,
            "singular": True,
        }

    if len(explicit_owner_candidates) > 1:
        return {
            "owner": "AMBIGUOUS_MULTIPLE_EXPLICIT_ITEMS",
            "source_type": "canonical_item",
            "evidence_files": evidence,
            "singular": False,
        }

    # No explicit owner in canonical item authority.
    fallback_files = [
        "docs/system_milestone_roadmap.md",
        "docs/athlete_analytics_branch.md",
    ]
    fallback_hits: list[str] = []
    for rel in fallback_files:
        path = REPO_ROOT / rel
        if path.exists():
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
            if "knowledge / reconciliation" in text or "knowledge" in text:
                fallback_hits.append(rel)

    return {
        "owner": "NONE_EXPLICIT_OWNER",
        "source_type": "no_explicit_canonical_item_owner",
        "evidence_files": [str(p.relative_to(REPO_ROOT)) for p in item_files[:5]] + fallback_hits,
        "singular": False,
    }


def owner_check(finish_message: str, expected_owner: str) -> tuple[bool, str]:
    low = finish_message.lower()
    if expected_owner == "NONE_EXPLICIT_OWNER":
        none_tokens = [
            "none_explicit_owner",
            "no explicit",
            "not explicitly",
            "no canonical item",
        ]
        ok = any(tok in low for tok in none_tokens)
        return ok, finish_message[:4000]
    # Require explicit RM-id or explicit item path citation.
    pattern = re.escape(expected_owner.lower())
    ok = re.search(pattern, low) is not None or f"docs/roadmap/items/{expected_owner.lower()}.md" in low
    return ok, finish_message[:4000]


def main() -> int:
    lan_url = detect_lan_url()
    canonical_owner = determine_canonical_owner()
    expected_owner = str(canonical_owner["owner"])
    results: dict[str, object] = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "checks": {},
        "urls": {"localhost": HOST_URL, "lan": lan_url or "not-detected"},
        "canonical_owner_determination": canonical_owner,
    }

    checks = results["checks"]

    ok, out = cmd_ok(["docker", "ps", "--filter", "name=^openhands-app$", "--format", "{{.Names}}|{{.Status}}|{{.Ports}}"])
    checks["container_running"] = {"ok": ok and "openhands-app|" in out and "Up " in out, "detail": out}

    ok, out = cmd_ok(["curl", "-fsS", HOST_URL])
    checks["http_localhost"] = {"ok": ok and len(out) > 0, "detail": out[:300]}

    if lan_url:
        ok, out = cmd_ok(["curl", "-fsS", lan_url])
        checks["http_lan"] = {"ok": ok and len(out) > 0, "detail": out[:300]}
    else:
        checks["http_lan"] = {"ok": False, "detail": "LAN host could not be detected; set OPENHANDS_LAN_HOST"}

    ok, out = cmd_ok(
        [
            "docker",
            "exec",
            "openhands-app",
            "python",
            "-c",
            "import urllib.request;print(urllib.request.urlopen('http://host.docker.internal:11434/api/tags',timeout=10).read().decode())",
        ]
    )
    checks["ollama_from_app"] = {"ok": ok and "qwen2.5-coder:32b" in out, "detail": out[:1000]}

    ok, out = cmd_ok(
        [
            "docker",
            "inspect",
            "openhands-app",
            "--format",
            "{{range .Mounts}}{{if eq .Destination \"/opt/workspace\"}}{{.Source}} -> {{.Destination}}{{end}}{{end}}",
        ]
    )
    checks["workspace_mount"] = {
        "ok": ok and "/Users/admin/repos/integrated-ai-platform -> /opt/workspace" in out,
        "detail": out,
    }

    inspect_proc = run(["bin/oss_wave_openhands.sh", "validate-inspect"], check=False)
    checks["inspect_prompt_exec"] = {
        "ok": inspect_proc.returncode == 0,
        "returncode": inspect_proc.returncode,
    }

    finish_message = ""
    scored_message = ""
    sessions = sorted(
        glob.glob(str(REPO_ROOT / ".local-model-data" / "openhands-state" / "sessions" / "*")),
        key=os.path.getmtime,
    )
    if sessions:
        latest = sessions[-1]
        event_files = sorted(
            glob.glob(f"{latest}/events/*.json"),
            key=lambda p: int(Path(p).stem),
        )
        candidate_messages: list[str] = []
        for event_path in reversed(event_files):
            data = json.loads(Path(event_path).read_text(encoding="utf-8"))
            if data.get("action") == "message" and data.get("source") == "agent":
                msg = data.get("message", "")
                if msg:
                    candidate_messages.append(msg)
            if data.get("action") == "finish":
                finish_message = data.get("message", "")
        # Score the most substantive answer, not just the terminal finish line.
        for msg in candidate_messages:
            low = msg.lower()
            if ("1." in msg and "2." in msg and "3." in msg and "4." in msg) or "none_explicit_owner" in low:
                scored_message = msg
                break
        if not scored_message:
            scored_message = finish_message

    checks["inspect_prompt_has_citations"] = {
        "ok": any(token in scored_message for token in ["docs/", "AGENTS.md", "docs/roadmap/ITEMS/"]),
        "detail": scored_message[:4000],
    }
    owner_ok, owner_detail = owner_check(scored_message, expected_owner)
    checks["inspect_prompt_owner_correct"] = {
        "ok": owner_ok,
        "expected_owner": expected_owner,
        "detail": owner_detail,
    }
    checks["inspect_prompt_finish_message_present"] = {
        "ok": bool(finish_message),
        "detail": finish_message[:1000],
    }

    all_ok = all(v.get("ok") for v in checks.values() if isinstance(v, dict) and "ok" in v)
    results["accepted"] = bool(all_ok)

    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")

    print(str(ARTIFACT_PATH))
    if all_ok:
        print("OPENHANDS_ACCEPTED")
        return 0
    print("OPENHANDS_REJECTED")
    return 1


if __name__ == "__main__":
    sys.exit(main())
