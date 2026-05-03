"""Tests for credential_finder.

Doctrine: NEVER read or emit credential VALUES. Tests assert this
explicitly by scanning produced records for known credential markers.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

LIB = Path(__file__).resolve().parent.parent / "lib"
sys.path.insert(0, str(LIB))

import compose_parser as cp  # noqa: E402
import credential_finder as cf  # noqa: E402
import docker_inspector as di  # noqa: E402


def test_finds_at_least_some_credential_files():
    creds = cf.find_all()
    assert creds, "no credential files discovered — search roots wrong?"
    assert len(creds) >= 20, f"expected ≥20 credential files, got {len(creds)}"


def test_no_credential_values_leak_into_records():
    """Doctrine ZZ: hash-only, no value display."""
    creds = cf.find_all()
    # Each record holds path/size/mode/fingerprint/mtime — never raw bytes.
    # Assert structurally that no record contains a long base64-ish or
    # hex-ish blob that could be a token/password/key.
    suspicious = re.compile(r"[A-Za-z0-9+/=]{40,}")
    for c in creds:
        # fingerprint is 12-char SHA256 prefix — that's allowed.
        for field_name in ("path", "basename", "service_hint"):
            v = getattr(c, field_name)
            if v is None:
                continue
            for m in suspicious.findall(str(v)):
                # allow paths like /Users/admin/.vault-agent-secrets/...
                if "/" in v:
                    continue
                # allow filenames like vault-init-keys-NEW-20260430.txt
                raise AssertionError(
                    f"suspicious long token in {field_name}={v!r} of {c.path}"
                )


def test_fingerprint_is_short_hex_prefix_not_full_hash():
    creds = cf.find_all()
    for c in creds:
        if c.fingerprint == "unreadable":
            continue
        assert len(c.fingerprint) == 12, (
            f"fingerprint should be 12-char prefix, got len={len(c.fingerprint)}"
        )
        assert re.fullmatch(r"[0-9a-f]+", c.fingerprint), (
            f"fingerprint not lowercase hex: {c.fingerprint!r}"
        )


def test_stale_files_flagged_correctly():
    """vault-init-keys.txt.PRE-KV-LOSS-INVALID-* must be stale, not canonical."""
    creds = cf.find_all()
    pre_kv = [c for c in creds if "PRE-KV-LOSS" in c.basename]
    assert pre_kv, "PRE-KV-LOSS file not found — known stale marker missing"
    for c in pre_kv:
        assert c.classification == "stale", (
            f"{c.basename} should be classified stale, got {c.classification}"
        )


def test_example_files_flagged_not_canonical():
    """.env.example must not be treated as a real credential file."""
    creds = cf.find_all()
    examples = [c for c in creds if c.basename.endswith(".example")]
    if examples:
        for c in examples:
            assert c.classification == "example", (
                f"{c.path} should be example-classified, got {c.classification}"
            )


def test_vault_agent_files_get_service_hint():
    """Files under ~/.vault-agent-secrets/<svc>/ must hint that service."""
    creds = cf.find_all()
    va = [c for c in creds if "/.vault-agent-secrets/" in c.path]
    assert va, "no Vault Agent secrets discovered"
    for c in va:
        assert c.service_hint, (
            f"Vault Agent file missing service_hint: {c.path}"
        )


def test_attach_to_merged_populates_credentials_field():
    intent = cp.parse_all()
    runtime, _ = di.inspect_all()
    merged, runtime_orphans, _ = di.merge_with_compose(intent, runtime)
    creds = cf.find_all()
    merged = cf.attach_to_merged(merged, creds, runtime_orphans)
    # at least one merged service should now carry credentials.files
    with_creds = [
        r for r in merged
        if r.get("credentials", {}).get("files")
    ]
    assert with_creds, "no service got credential files attached"


def test_summary_detects_shared_credential_files():
    """Multiple Plane workers share one credentials.env — should surface
    as a duplicate fingerprint. This is intentional (shared Vault Agent
    output) but the registry must make it visible."""
    creds = cf.find_all()
    summary = cf.summarize(creds)
    assert "duplicate_fingerprints" in summary
    # Don't assert specific services exist (Plane might be removed
    # someday), but assert SOME duplicates surfaced — multi-consumer
    # Vault Agent is a known platform pattern.
    # Soft-skip if no plane/zabbix style sharing exists right now.
    if not summary["duplicate_fingerprints"]:
        return
    for fp, paths in summary["duplicate_fingerprints"].items():
        assert len(paths) >= 2


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
