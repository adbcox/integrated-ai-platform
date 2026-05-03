"""Integration tests for docker_inspector + merge against current platform."""

from __future__ import annotations

import sys
from pathlib import Path

LIB = Path(__file__).resolve().parent.parent / "lib"
sys.path.insert(0, str(LIB))

import compose_parser as cp  # noqa: E402
import docker_inspector as di  # noqa: E402


def test_docker_reachable():
    runtime, errs = di.inspect_all()
    assert runtime, f"no runtime records — docker daemon unreachable? errs={errs}"


def test_runtime_has_seal_vault():
    runtime, _ = di.inspect_all()
    sv = [r for r in runtime if r.container_name == "seal-vault"]
    assert sv, "seal-vault container not running"
    assert sv[0].state_status == "running"


def test_seal_vault_actual_port_is_8201_not_8200():
    """The canonical example. Tonight's 3h failure mode prevented."""
    runtime, _ = di.inspect_all()
    sv = [r for r in runtime if r.container_name == "seal-vault"]
    assert sv
    host_ports = {b["host_port"] for b in sv[0].actual_port_bindings if b.get("host_port")}
    assert 8201 in host_ports, (
        f"seal-vault expected to expose host port 8201 (D-17-28 finding); got {host_ports}"
    )
    # And 8200 is NOT bound — that's the AI's wrong default.
    assert 8200 not in host_ports, (
        f"seal-vault should NOT bind 8200; got {host_ports}"
    )


def test_merge_matches_seal_vault_intent_to_runtime():
    intent = cp.parse_all()
    runtime, _ = di.inspect_all()
    merged, _, _ = di.merge_with_compose(intent, runtime)
    sv = [r for r in merged if r["service_id"] == "seal-vault"]
    assert sv
    rec = sv[0]
    assert rec["state"]["status"] == "running"
    assert any(
        m["host_port"] == 8201 for m in rec["addresses"]["host_mapped"]
    ), f"merged record missing host_port=8201; got {rec['addresses']['host_mapped']}"


def test_orphans_are_known_non_compose_containers():
    """Per CLAUDE.md D#30: sms1obot-* are non-compose. (mcp-docker-remote
    was migrated to compose at docker/mcp/docker-compose.mcp-docker-remote.yml,
    so no longer appears as orphan.)"""
    intent = cp.parse_all()
    runtime, _ = di.inspect_all()
    _, orphans, _ = di.merge_with_compose(intent, runtime)
    orphan_names = {o["container_name"] for o in orphans}
    # sms1obot containers are Obot-managed; expected to be orphans
    assert any("sms1obot" in n for n in orphan_names), (
        f"sms1obot containers expected as orphans; got {sorted(orphan_names)}"
    )


def test_merged_record_has_required_schema_keys():
    """Per spec §5 — every record carries the canonical keys."""
    intent = cp.parse_all()
    runtime, _ = di.inspect_all()
    merged, _, _ = di.merge_with_compose(intent, runtime)
    required = {
        "service_id",
        "container_name",
        "stack",
        "compose_file",
        "image",
        "state",
        "addresses",
        "credentials",
        "depends_on",
        "depended_on_by",
        "known_failure_modes",
        "access_examples",
        "documentation_refs",
    }
    for r in merged:
        missing = required - set(r.keys())
        assert not missing, f"{r['service_id']} missing keys: {missing}"


def test_dependency_back_links_populated():
    intent = cp.parse_all()
    runtime, _ = di.inspect_all()
    merged, _, _ = di.merge_with_compose(intent, runtime)
    by = {r["service_id"]: r for r in merged}
    # Pick any service with depends_on; its target's depended_on_by must include it
    for r in merged:
        for dep in r["depends_on"]:
            if dep in by:
                assert r["service_id"] in by[dep]["depended_on_by"], (
                    f"{r['service_id']} depends_on {dep}, but {dep}'s depended_on_by missing it"
                )


if __name__ == "__main__":
    import traceback

    tests = [v for k, v in globals().items() if k.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL {t.__name__}: {e}")
        except Exception:
            failed += 1
            print(f"  ERROR {t.__name__}:")
            traceback.print_exc()
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
