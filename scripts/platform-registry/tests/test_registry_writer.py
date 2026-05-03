"""Integration tests for the full registry pipeline.

Spec §10 success criteria:
  1. seal-vault registry query returns host_port=8201 (NOT 8200) — the
     canonical D-17-28 prevention check.
  2. Dependency cascade: every depends_on target carries the back-link.
  3. Canonical credentials surface; stale ones are NOT attached.
  4. Refresh completes in <30 seconds (target: <5).
  5. Pipeline tolerates per-layer failure without aborting (compose
     parser failure should not blank the runtime layer, etc.).
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import time
from pathlib import Path

LIB = Path(__file__).resolve().parent.parent / "lib"
sys.path.insert(0, str(LIB))

import registry_writer as rw  # noqa: E402


def _tmp_output() -> Path:
    return Path(tempfile.mkdtemp(prefix="platform-registry-test-"))


def test_full_refresh_under_30_seconds():
    out = _tmp_output()
    try:
        t0 = time.monotonic()
        meta = rw.refresh(out)
        elapsed = time.monotonic() - t0
        assert elapsed < 30, f"refresh took {elapsed:.1f}s — over 30s budget"
        # belt-and-suspenders: metadata.elapsed should agree
        assert meta["elapsed_seconds"] < 30
    finally:
        shutil.rmtree(out, ignore_errors=True)


def test_seal_vault_registry_query_returns_8201_not_8200():
    """THE canonical example. Tonight's 3-hour failure mode prevented."""
    out = _tmp_output()
    try:
        rw.refresh(out)
        sv = rw.query("seal-vault", out)
        assert sv is not None, "seal-vault not in registry"
        host_ports = {
            hm["host_port"]
            for hm in sv["addresses"]["host_mapped"]
            if hm.get("host_port")
        }
        assert 8201 in host_ports, (
            f"seal-vault host_port should be 8201; got {host_ports}"
        )
        assert 8200 not in host_ports, (
            f"seal-vault must NOT bind 8200 (the AI's wrong default); got {host_ports}"
        )
    finally:
        shutil.rmtree(out, ignore_errors=True)


def test_inventory_and_per_service_files_written():
    out = _tmp_output()
    try:
        rw.refresh(out)
        assert (out / "inventory.json").exists()
        assert (out / "last-refresh.json").exists()
        assert (out / "by-service").is_dir()
        per_svc = list((out / "by-service").glob("*.json"))
        assert len(per_svc) >= 70, f"expected ≥70 per-service files, got {len(per_svc)}"
        # each per-service file is valid JSON with required schema keys
        sample = json.loads(per_svc[0].read_text())
        for k in ("service_id", "container_name", "state", "addresses"):
            assert k in sample
    finally:
        shutil.rmtree(out, ignore_errors=True)


def test_dependency_back_links_in_per_service_files():
    out = _tmp_output()
    try:
        rw.refresh(out)
        files = list((out / "by-service").glob("*.json"))
        all_recs = [json.loads(p.read_text()) for p in files]
        by_id = {r["service_id"]: r for r in all_recs}
        for r in all_recs:
            for dep in r.get("depends_on", []):
                tgt = by_id.get(dep)
                if tgt is None:
                    continue
                assert r["service_id"] in tgt["depended_on_by"], (
                    f"{r['service_id']} depends_on {dep}, but back-link missing"
                )
    finally:
        shutil.rmtree(out, ignore_errors=True)


def test_canonical_credentials_attach_stale_do_not():
    out = _tmp_output()
    try:
        rw.refresh(out)
        files = list((out / "by-service").glob("*.json"))
        for p in files:
            rec = json.loads(p.read_text())
            for cf in (rec.get("credentials") or {}).get("files", []):
                assert cf["classification"] == "canonical", (
                    f"non-canonical credential attached to {rec['service_id']}: "
                    f"{cf}"
                )
                # value-leak guard: no key named 'value', 'token', 'secret'
                forbidden = {"value", "token", "secret", "password", "key"}
                assert not (set(cf.keys()) & forbidden), (
                    f"forbidden credential key in {rec['service_id']}: {cf.keys()}"
                )
    finally:
        shutil.rmtree(out, ignore_errors=True)


def test_metadata_counts_internally_consistent():
    out = _tmp_output()
    try:
        meta = rw.refresh(out)
        c = meta["counts"]
        assert c["intent_services"] >= 70
        assert c["runtime_containers"] >= c["merged_services"], (
            f"runtime ({c['runtime_containers']}) should be ≥ merged ({c['merged_services']})"
        )
        assert c["caddy_routes"] >= c["caddy_routes"] - c["caddy_orphans"]
        full = json.loads((out / "inventory.json").read_text())
        assert len(full["services"]) == c["merged_services"]
        assert len(full["runtime_orphans"]) == c["runtime_orphans"]
    finally:
        shutil.rmtree(out, ignore_errors=True)


def test_query_returns_none_for_unknown_service():
    out = _tmp_output()
    try:
        rw.refresh(out)
        assert rw.query("definitely-not-a-real-service", out) is None
    finally:
        shutil.rmtree(out, ignore_errors=True)


def test_refresh_overwrites_old_per_service_files():
    """Stale per-service files from a previous run must be cleaned out."""
    out = _tmp_output()
    try:
        # seed an old file
        (out / "by-service").mkdir(parents=True, exist_ok=True)
        stale = out / "by-service" / "ghost-service.json"
        stale.write_text('{"ghost": true}')
        rw.refresh(out)
        assert not stale.exists(), "stale per-service file not cleaned up"
    finally:
        shutil.rmtree(out, ignore_errors=True)


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
