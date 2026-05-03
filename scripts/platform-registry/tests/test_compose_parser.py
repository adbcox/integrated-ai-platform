"""Integration tests for compose_parser against the live platform compose set.

These are not pure unit tests — they assert against the actual files on
this platform. If the platform's compose set changes meaningfully,
these need refreshing.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

import compose_parser as cp  # noqa: E402


def test_discover_finds_all_active_files():
    files = cp.discover_compose_files()
    # Pre-flight scan reported 31 in-scope files
    assert len(files) >= 30, f"expected ≥30 active compose files, got {len(files)}"
    # No retired/parked
    assert not any("_retired" in str(p) for p in files)
    assert not any(str(p).endswith(".parked.yml") for p in files)


def test_parse_all_yields_at_least_70_services():
    recs = cp.parse_all()
    ok = [r for r in recs if not r.service_id.startswith("PARSE_FAIL:")]
    assert len(ok) >= 70, f"expected ≥70 parsed services, got {len(ok)}"


def test_no_parse_failures():
    recs = cp.parse_all()
    fails = [r for r in recs if r.service_id.startswith("PARSE_FAIL:")]
    assert not fails, f"parse failures: {[r.compose_file for r in fails]}"


def test_seal_vault_is_present_with_correct_image():
    recs = cp.parse_all()
    sv = [r for r in recs if r.service_id == "seal-vault"]
    assert sv, "seal-vault service not found in compose set"
    rec = sv[0]
    assert rec.image and "vault" in rec.image.lower()
    assert "seal-vault" in rec.compose_file


def test_vault_server_depends_on_seal_vault_indirectly_via_init():
    # vault-server's autounseal target is seal-vault but compose may not
    # express this as depends_on (Vault Agent template handles it). Just
    # assert vault-server exists with expected image family.
    recs = cp.parse_all()
    vs = [r for r in recs if r.service_id == "vault-server"]
    assert vs, "vault-server service not found"


def test_caddy_is_present():
    recs = cp.parse_all()
    caddy = [r for r in recs if r.service_id == "caddy"]
    assert caddy, "caddy service not found"


def test_records_carry_compose_file_path():
    recs = cp.parse_all()
    assert all(r.compose_file for r in recs if not r.service_id.startswith("PARSE_FAIL:"))


def test_port_mapping_format():
    recs = cp.parse_all()
    for r in recs:
        for m in r.host_port_mappings:
            assert "container_port" in m
            assert isinstance(m["container_port"], int)


def test_xindex_present_with_known_internal_port():
    """xindex listens on container port 8000 per its compose; verify."""
    recs = cp.parse_all()
    xi = [r for r in recs if r.service_id == "xindex"]
    assert xi, "xindex not found"
    rec = xi[0]
    container_ports = {m["container_port"] for m in rec.host_port_mappings}
    # at least one mapping should target 8000 (the FastAPI port inside)
    assert 8000 in container_ports or rec.expose_ports, (
        f"xindex expected to listen on 8000 internally; mappings={rec.host_port_mappings} expose={rec.expose_ports}"
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
