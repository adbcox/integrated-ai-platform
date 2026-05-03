"""Registry writer — full pipeline + JSON output.

Per Service Registry MVP spec §5 + §6. Pipes:
  compose_parser  →  intent records
  docker_inspector →  runtime records, merged with intent
  caddy_reader    →  external routing (admin API or Caddyfile)
  credential_finder →  credential metadata (no values)

Output tree (default ~/.platform-registry/):
  inventory.json              — full snapshot, all services + meta
  by-service/<service_id>.json — per-service slices (one file each)
  last-refresh.json           — refresh timestamp + counts + errors
"""

from __future__ import annotations

import datetime as dt
import json
import sys
import time
from pathlib import Path
from typing import Any

LIB = Path(__file__).resolve().parent
sys.path.insert(0, str(LIB))

import caddy_reader as cr  # noqa: E402
import compose_parser as cp  # noqa: E402
import credential_finder as cf  # noqa: E402
import docker_inspector as di  # noqa: E402

DEFAULT_OUTPUT = Path.home() / ".platform-registry"


def build_registry() -> tuple[dict, dict]:
    """Run the full pipeline. Return (registry, metadata)."""
    t0 = time.monotonic()
    errors: list[str] = []

    # Layer 1: intent
    intent = cp.parse_all()
    intent_ok = [r for r in intent if not r.service_id.startswith("PARSE_FAIL:")]
    intent_fails = [r for r in intent if r.service_id.startswith("PARSE_FAIL:")]
    for f in intent_fails:
        errors.append(f"compose parse fail: {f.compose_file}")

    # Layer 2: runtime + merge
    runtime, run_errs = di.inspect_all()
    errors.extend(run_errs)
    merged, runtime_orphans, merge_warnings = di.merge_with_compose(intent_ok, runtime)
    errors.extend(merge_warnings)

    # Layer 3: caddy
    caddy_routes, caddy_src = cr.read_routes()
    merged, caddy_orphans = cr.attach_to_merged(merged, caddy_routes, runtime_orphans)

    # Layer 4: credentials
    creds = cf.find_all()
    merged = cf.attach_to_merged(merged, creds, runtime_orphans)
    cred_summary = cf.summarize(creds)

    elapsed = round(time.monotonic() - t0, 3)

    registry = {
        "schema_version": "1.0",
        "services": merged,
        "runtime_orphans": runtime_orphans,
        "caddy_orphans": caddy_orphans,
        "credentials_summary": cred_summary,
    }

    metadata = {
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "elapsed_seconds": elapsed,
        "counts": {
            "compose_files": len({r.compose_file for r in intent_ok}),
            "intent_services": len(intent_ok),
            "runtime_containers": len(runtime),
            "merged_services": len(merged),
            "runtime_orphans": len(runtime_orphans),
            "caddy_routes": len(caddy_routes),
            "caddy_orphans": len(caddy_orphans),
            "credential_files": cred_summary.get("total", 0),
        },
        "caddy_source": caddy_src,
        "errors": errors,
    }

    return registry, metadata


def write_registry(
    registry: dict, metadata: dict, output_dir: Path = DEFAULT_OUTPUT
) -> dict[str, Path]:
    """Write inventory.json + by-service/*.json + last-refresh.json.
    Returns paths written."""
    output_dir.mkdir(parents=True, exist_ok=True)
    by_svc_dir = output_dir / "by-service"
    by_svc_dir.mkdir(exist_ok=True)

    inventory_path = output_dir / "inventory.json"
    refresh_path = output_dir / "last-refresh.json"

    full = {**registry, "metadata": metadata}
    inventory_path.write_text(json.dumps(full, indent=2, default=str))
    refresh_path.write_text(json.dumps(metadata, indent=2, default=str))

    # per-service slices — wipe + rewrite to drop deleted services
    for old in by_svc_dir.glob("*.json"):
        old.unlink()
    paths: dict[str, Path] = {
        "inventory": inventory_path,
        "last-refresh": refresh_path,
    }
    for svc in registry["services"]:
        sid = _safe_filename(svc["service_id"])
        p = by_svc_dir / f"{sid}.json"
        p.write_text(json.dumps(svc, indent=2, default=str))
        paths[svc["service_id"]] = p
    return paths


def _safe_filename(s: str) -> str:
    return "".join(c if c.isalnum() or c in "-_." else "_" for c in s)


def query(service_id: str, output_dir: Path = DEFAULT_OUTPUT) -> dict | None:
    """Convenience reader for a single service. Used by tests + AI consultation."""
    p = output_dir / "by-service" / f"{_safe_filename(service_id)}.json"
    if not p.exists():
        return None
    return json.loads(p.read_text())


def refresh(output_dir: Path = DEFAULT_OUTPUT) -> dict:
    """Build + write registry. Return metadata."""
    registry, metadata = build_registry()
    write_registry(registry, metadata, output_dir)
    return metadata


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUTPUT
    meta = refresh(out)
    print(json.dumps(meta, indent=2, default=str))
