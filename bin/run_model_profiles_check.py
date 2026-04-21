#!/usr/bin/env python3
"""P1-01: Validate model profiles YAML and emit validation artifact."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

PROFILES_PATH = REPO_ROOT / "governance/model_profiles.v1.yaml"
ARTIFACT_PATH = REPO_ROOT / "artifacts/governance/model_profiles_validation.json"

GROUNDING_INPUTS = [
    REPO_ROOT / "governance/cmdb_lite_registry.v1.yaml",
    REPO_ROOT / "governance/autonomy_scorecard.v1.yaml",
    REPO_ROOT / "governance/definition_of_done.v1.yaml",
    REPO_ROOT / "docs/specs/cmdb_lite_registry.md",
    REPO_ROOT / "artifacts/governance/core_adr_index.json",
]

REQUIRED_SECTIONS = ["version", "default_backend", "profiles", "routing_notes", "exceptions"]

REQUIRED_PROFILES = ["fast", "balanced", "hard", "long_context"]

REQUIRED_PROFILE_FIELDS = [
    "profile_id",
    "backend",
    "model_name",
    "context_window",
    "timeout_seconds",
    "temperature_policy",
    "intended_task_class",
    "enabled",
]


def _load_yaml(path: Path):
    try:
        import yaml  # type: ignore
        return yaml.safe_load(path.read_text(encoding="utf-8")), None
    except ImportError:
        pass
    return _minimal_yaml_keys(path.read_text(encoding="utf-8")), None


def _minimal_yaml_keys(text: str) -> dict:
    import re
    keys: dict = {}
    for line in text.splitlines():
        if line.startswith("#") or not line.strip():
            continue
        m = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*:', line)
        if m:
            keys[m.group(1)] = True
    return keys


def _verify_grounding() -> bool:
    all_ok = True
    for p in GROUNDING_INPUTS:
        ok = p.exists() and p.stat().st_size > 50
        print(f"  grounding [{'OK' if ok else 'FAIL'}]: {p.relative_to(REPO_ROOT)}")
        if not ok:
            all_ok = False
    return all_ok


def _check_content(mp: dict) -> tuple[bool, list[str]]:
    errors: list[str] = []

    # default_backend must be ollama
    if mp.get("default_backend") != "ollama":
        errors.append(f"default_backend must be 'ollama', got {mp.get('default_backend')!r}")

    # profiles section
    profiles = mp.get("profiles", {})
    if not isinstance(profiles, dict):
        errors.append("profiles must be a mapping")
        return False, errors

    for pid in REQUIRED_PROFILES:
        if pid not in profiles:
            errors.append(f"profiles missing required profile: {pid}")
        else:
            entry = profiles[pid]
            if not isinstance(entry, dict):
                errors.append(f"profiles.{pid} must be a mapping")
                continue
            for field in REQUIRED_PROFILE_FIELDS:
                if field not in entry:
                    errors.append(f"profiles.{pid} missing required field: {field}")
            # profile_id must match key
            if entry.get("profile_id") != pid:
                errors.append(f"profiles.{pid}.profile_id must equal '{pid}', got {entry.get('profile_id')!r}")
            # backend must be ollama
            if entry.get("backend") != "ollama":
                errors.append(f"profiles.{pid}.backend must be 'ollama', got {entry.get('backend')!r}")

    # At least one profile for narrow routine tasks
    narrow_profiles = [
        pid for pid in REQUIRED_PROFILES
        if isinstance(profiles.get(pid), dict)
        and any("narrow_routine" in tc or "guard_clause" in tc or "single_file" in tc
                for tc in (profiles[pid].get("intended_task_class") or []))
    ]
    if not narrow_profiles:
        errors.append("no profile found with narrow_routine or equivalent intended_task_class")

    # At least one profile for harder/longer-context work
    harder_profiles = [
        pid for pid in REQUIRED_PROFILES
        if isinstance(profiles.get(pid), dict)
        and any("complex" in tc or "large_context" in tc or "hard" in tc or "long" in tc
                for tc in (profiles[pid].get("intended_task_class") or []))
    ]
    if not harder_profiles:
        errors.append("no profile found with complex/harder/long_context intended_task_class")

    # exceptions must mention claude not being a routine profile
    exceptions = mp.get("exceptions", {})
    if not isinstance(exceptions, dict):
        errors.append("exceptions must be a mapping")
    else:
        if "claude_is_not_a_routine_profile" not in exceptions:
            errors.append("exceptions missing required key: claude_is_not_a_routine_profile")

    return len(errors) == 0, errors


def main() -> None:
    print("P1-01: verifying grounding inputs...")
    if not _verify_grounding():
        print("HARD STOP: grounding inputs missing", file=sys.stderr)
        sys.exit(1)

    print("Loading model profiles YAML...")
    mp, err = _load_yaml(PROFILES_PATH)
    if mp is None:
        print(f"HARD STOP: profiles load failed: {err}", file=sys.stderr)
        sys.exit(1)
    print(f"  yaml loaded: {PROFILES_PATH.relative_to(REPO_ROOT)}")

    print("Checking required sections...")
    missing = [s for s in REQUIRED_SECTIONS if s not in mp]
    if missing:
        print(f"HARD STOP: missing sections: {missing}", file=sys.stderr)
        sys.exit(1)
    print(f"  required_sections_present: True ({len(REQUIRED_SECTIONS)} sections)")

    print("Checking required profiles and fields...")
    ok, content_errors = _check_content(mp)
    if not ok:
        for e in content_errors:
            print(f"  FAIL: {e}", file=sys.stderr)
        print("HARD STOP: content check failed", file=sys.stderr)
        sys.exit(1)
    print(f"  required_profiles_present: True ({len(REQUIRED_PROFILES)} profiles)")
    print(f"  required_fields_present: True ({len(REQUIRED_PROFILE_FIELDS)} fields per profile)")

    artifact = {
        "artifact_id": "P1-01-MODEL-PROFILES-VALIDATION-1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "profiles_path": str(PROFILES_PATH.relative_to(REPO_ROOT)),
        "yaml_loaded": True,
        "required_profiles_checked": REQUIRED_PROFILES,
        "required_profiles_present": True,
        "required_fields_checked": REQUIRED_PROFILE_FIELDS,
        "required_fields_present": True,
        "content_errors": [],
        "phase_linkage": "Phase 1 (runtime_contract_foundation)",
        "authority_sources": [
            "ADR-0004",
            "governance/cmdb_lite_registry.v1.yaml",
            "governance/definition_of_done.v1.yaml",
            "governance/autonomy_scorecard.v1.yaml",
        ],
    }

    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_PATH.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    print(f"artifact:   {ARTIFACT_PATH.relative_to(REPO_ROOT)}")
    print("P1-01: all checks passed.")


if __name__ == "__main__":
    main()
