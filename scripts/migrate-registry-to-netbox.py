#!/usr/bin/env python3
"""Block 4.C C3.2 — migrate config/service-registry.yaml into NetBox.

Plan:
  1. Ensure 1 site (`integrated-ai-platform`) exists.
  2. Ensure 1 device per host (mac-mini, qnap, ha-device, opnsense),
     each with a stub manufacturer / device type / device role.
  3. For each registry service, create or update an `ipam.service`
     attached to its host device. Custom fields receive the long-form
     metadata; native ports come from `port` (fallback `internal_port`);
     tags get `category`, `kind`, and `deprecated` where applicable.
  4. Second pass: resolve `depends_on` into the multi-object
     `service_dependencies` custom field (NetBox object IDs).

Idempotent: every create-or-update is keyed by a stable name so
repeat runs are no-ops.

Modes:
  --dry-run    print planned creates / updates / skips, touch nothing.
  (default)    apply.

Token sourced from /Users/admin/.vault-agent-secrets/netbox/credentials.env.
Run from the Mac Mini in the block-4c venv.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import pynetbox  # type: ignore
import yaml

NETBOX_URL = os.environ.get("NETBOX_URL", "http://localhost:8084")
CRED_FILE = Path("/Users/admin/.vault-agent-secrets/netbox/credentials.env")
REGISTRY_FILE = Path("config/service-registry.yaml")

SITE_SLUG = "integrated-ai-platform"
SITE_NAME = "Integrated AI Platform"
MANUFACTURER_SLUG = "platform-host"
DEVICE_TYPE_SLUG = "platform-host"
DEVICE_ROLE_SLUG = "platform-host"


def load_token() -> str:
    """Return the full V2 wire token (nbt_<key>.<secret>) for API auth."""
    if not CRED_FILE.is_file():
        sys.exit(f"ERROR: credentials file {CRED_FILE} missing")
    fields: dict[str, str] = {}
    for line in CRED_FILE.read_text().splitlines():
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        fields[k.strip()] = v.strip()
    if "NETBOX_API_TOKEN" in fields:
        return fields["NETBOX_API_TOKEN"]
    sys.exit("ERROR: NETBOX_API_TOKEN missing from credentials.env (Block 4.C C3 update required)")


def load_registry() -> list[dict]:
    """Load services, de-duplicating by id (last-wins, with a warning logged
    once per duplicate id — per C1 audit Finding A)."""
    if not REGISTRY_FILE.is_file():
        sys.exit(f"ERROR: registry {REGISTRY_FILE} missing — run from repo root")
    data = yaml.safe_load(REGISTRY_FILE.read_text())
    raw = data.get("services") or []
    seen: dict[str, dict] = {}
    dups: set[str] = set()
    for s in raw:
        sid = s.get("id")
        if sid in seen:
            dups.add(sid)
        seen[sid] = s
    if dups:
        for d in sorted(dups):
            print(f"  NOTE: duplicate id '{d}' in registry — using last entry (C1 audit Finding A)")
    return list(seen.values())


# ── Plan accumulator ────────────────────────────────────────────────
class Plan:
    def __init__(self, dry_run: bool):
        self.dry_run = dry_run
        self.actions: list[tuple[str, str, str]] = []  # (verb, type, name)

    def record(self, verb: str, kind: str, name: str) -> None:
        self.actions.append((verb, kind, name))
        prefix = "DRY-RUN" if self.dry_run else "APPLY  "
        print(f"  {prefix}  {verb:<8} {kind:<18} {name}")

    def summary(self) -> str:
        c = Counter((v, t) for v, t, _ in self.actions)
        lines = [f"  {v:<8} {t:<18} {n}" for (v, t), n in sorted(c.items())]
        return "\n".join(lines) if lines else "  (no actions)"


# ── Idempotent upserts ─────────────────────────────────────────────
def upsert(plan: Plan, kind: str, key: dict, payload: dict, endpoint, name_for_log: str):
    """Find by key; create or update payload. Returns the object (or None on dry-run-create)."""
    existing = endpoint.get(**key)
    if existing:
        diff = {k: v for k, v in payload.items() if getattr(existing, k, None) != v and k not in ("custom_fields",)}
        # custom_fields require deep-comparison
        if "custom_fields" in payload:
            existing_cf = getattr(existing, "custom_fields", {}) or {}
            new_cf = payload["custom_fields"]
            cf_diff = {k: v for k, v in new_cf.items() if existing_cf.get(k) != v}
            if cf_diff:
                diff["custom_fields"] = cf_diff
        if not diff:
            plan.record("skip", kind, name_for_log)
            return existing
        plan.record("update", kind, name_for_log)
        if not plan.dry_run:
            existing.update(payload)
        return existing
    plan.record("create", kind, name_for_log)
    if plan.dry_run:
        return None
    return endpoint.create(payload)


def ensure_site(nb, plan: Plan):
    return upsert(plan, "site", {"slug": SITE_SLUG},
                  {"name": SITE_NAME, "slug": SITE_SLUG, "status": "active"},
                  nb.dcim.sites, SITE_SLUG)


def ensure_manufacturer(nb, plan: Plan):
    return upsert(plan, "manufacturer", {"slug": MANUFACTURER_SLUG},
                  {"name": "Platform Host", "slug": MANUFACTURER_SLUG},
                  nb.dcim.manufacturers, MANUFACTURER_SLUG)


def ensure_device_type(nb, plan: Plan, manufacturer_id: int | None):
    payload = {"model": "Platform Host", "slug": DEVICE_TYPE_SLUG}
    if manufacturer_id is not None:
        payload["manufacturer"] = manufacturer_id
    return upsert(plan, "device_type", {"slug": DEVICE_TYPE_SLUG},
                  payload, nb.dcim.device_types, DEVICE_TYPE_SLUG)


def ensure_device_role(nb, plan: Plan):
    return upsert(plan, "device_role", {"slug": DEVICE_ROLE_SLUG},
                  {"name": "Platform Host", "slug": DEVICE_ROLE_SLUG, "color": "2196f3"},
                  nb.dcim.device_roles, DEVICE_ROLE_SLUG)


def ensure_device(nb, plan: Plan, host_name: str, site_id, role_id, dtype_id):
    payload = {
        "name": host_name,
        "site": site_id,
        "role": role_id,
        "device_type": dtype_id,
        "status": "active",
    }
    return upsert(plan, "device", {"name": host_name},
                  payload, nb.dcim.devices, host_name)


# ── Service shape conversion ────────────────────────────────────────
def normalize_credentials(svc: dict) -> str:
    """Combine credentials_env list and credentials list (filtered) into one
    newline-separated string for the vault_paths longtext custom field."""
    parts: list[str] = []
    env = svc.get("credentials_env") or []
    if isinstance(env, list):
        parts.extend(env)
    creds = svc.get("credentials")
    if isinstance(creds, list):
        parts.extend(creds)
    elif isinstance(creds, str) and creds.lower() != "none":
        parts.append(creds)
    return "\n".join(parts)


def build_service_payload(svc: dict, device_id: int, tag_ids: dict[str, int]) -> dict:
    port = svc.get("port") or svc.get("internal_port") or 0
    if not isinstance(port, int) or port <= 0:
        port = svc.get("internal_port") or 0
    if not isinstance(port, int) or port <= 0:
        # Sentinel for port-less services (workers, sidecars). NetBox
        # ipam.service.ports is required+non-empty. Port 1 is reserved
        # (tcpmux, RFC1340) so it cannot collide with a real binding.
        port = 1
    name = svc.get("id")
    description = svc.get("name") or svc["id"]
    purpose = svc.get("purpose") or ""
    notes = svc.get("notes") or ""
    comments = purpose
    if notes:
        comments = (comments + "\n\n" + notes).strip() if comments else notes

    # Tags: category + kind + deprecated
    tag_slugs: list[int] = []
    cat = svc.get("category")
    if cat and cat in tag_ids:
        tag_slugs.append(tag_ids[cat])
    kind = svc.get("kind")
    if kind and kind in tag_ids:
        tag_slugs.append(tag_ids[kind])
    if svc.get("deprecated"):
        tag_slugs.append(tag_ids["deprecated"])

    health_expect = svc.get("health_expect")
    if isinstance(health_expect, list) and health_expect:
        health_expect = health_expect[0]
    if not isinstance(health_expect, int):
        try:
            health_expect = int(health_expect) if health_expect else 0
        except (TypeError, ValueError):
            health_expect = 0

    cf: dict[str, Any] = {
        "registry_id": svc["id"],
        "container_name": svc.get("container") or "",
        "container_image": svc.get("image") or "",
        "health_url": svc.get("health_url") or "",
        "health_method": svc.get("health_method") or "",
        "health_expect": health_expect,
        "compose_file": svc.get("compose_file") or "",
        "vault_paths": normalize_credentials(svc),
        "security_profile": json.dumps(svc.get("security") or {}, sort_keys=True),
        "public_values": json.dumps(svc.get("public_values") or {}, sort_keys=True),
        "service_notes": notes,
        "sidecar_of": svc.get("sidecar_of") or "",
        "superseded_by": svc.get("superseded_by") or "",
        # service_dependencies set in second pass
    }

    payload: dict[str, Any] = {
        "name": name,
        # NetBox 4.5 generic-FK shape (parent_object_type / parent_object_id)
        "parent_object_type": "dcim.device",
        "parent_object_id": device_id,
        "protocol": "tcp",
        "ports": [port] if port > 0 else [],
        "description": description[:200],
        "comments": comments,
        "custom_fields": cf,
        "tags": [{"id": t} for t in tag_slugs],
    }
    return payload


# ── Main ──────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Plan only, no writes")
    args = ap.parse_args()

    token = load_token()
    nb = pynetbox.api(NETBOX_URL, token=token)
    plan = Plan(dry_run=args.dry_run)

    services = load_registry()
    print(f"Registry services: {len(services)}")
    print(f"NetBox URL: {NETBOX_URL}")
    print(f"Mode: {'DRY-RUN' if args.dry_run else 'APPLY'}\n")

    # Tag lookup (must already exist via netbox-custom-fields.py)
    tag_ids: dict[str, int] = {}
    for tag in nb.extras.tags.all():
        tag_ids[tag.slug] = tag.id
        tag_ids[tag.name] = tag.id

    print("── Site / device-type / role / manufacturer ──────────────")
    site = ensure_site(nb, plan)
    mfr = ensure_manufacturer(nb, plan)
    dtype = ensure_device_type(nb, plan, getattr(mfr, "id", None) if mfr else None)
    role = ensure_device_role(nb, plan)

    site_id = getattr(site, "id", 0)
    role_id = getattr(role, "id", 0)
    dtype_id = getattr(dtype, "id", 0)

    print("\n── Devices (one per registry host) ───────────────────────")
    hosts = sorted({s.get("host") for s in services if s.get("host")})
    devices: dict[str, Any] = {}
    for h in hosts:
        devices[h] = ensure_device(nb, plan, h, site_id, role_id, dtype_id)

    print("\n── Services (ipam.service per registry entry) ────────────")
    by_id: dict[str, Any] = {}
    for svc in services:
        host = svc.get("host")
        device = devices.get(host)
        device_id = getattr(device, "id", 0)
        if device_id == 0 and not args.dry_run:
            print(f"  WARN: device for host {host} not resolved (svc={svc['id']})")
        payload = build_service_payload(svc, device_id, tag_ids)
        obj = upsert(plan, "service", {"name": svc["id"]},
                     payload, nb.ipam.services, svc["id"])
        if obj:
            by_id[svc["id"]] = obj
        elif args.dry_run:
            # Dry-run create returns None; stub so the deps pass can plan
            class _Stub:
                pass
            stub = _Stub()
            stub.id = -1  # sentinel
            stub.custom_fields = {}
            by_id[svc["id"]] = stub

    print("\n── Service dependencies (multi-object cross-refs) ────────")
    for svc in services:
        deps = svc.get("depends_on") or []
        if not deps:
            continue
        target = by_id.get(svc["id"])
        if not target:
            plan.record("skip", "deps", f"{svc['id']} (no target)")
            continue
        dep_ids = []
        missing = []
        for d in deps:
            dep_obj = by_id.get(d)
            if dep_obj:
                dep_ids.append(dep_obj.id)
            else:
                missing.append(d)
        if missing:
            plan.record("warn", "deps", f"{svc['id']} missing→{missing}")
        if not dep_ids:
            continue
        existing_cf = getattr(target, "custom_fields", {}) or {}
        existing_deps = existing_cf.get("service_dependencies") or []
        existing_dep_ids = sorted(d.get("id") if isinstance(d, dict) else d for d in existing_deps)
        if existing_dep_ids == sorted(dep_ids):
            plan.record("skip", "deps", svc["id"])
            continue
        plan.record("update", "deps", f"{svc['id']} ({len(dep_ids)})")
        if not args.dry_run:
            target.update({"custom_fields": {"service_dependencies": dep_ids}})

    print("\n── Summary ────────────────────────────────────────────────")
    print(plan.summary())

    if args.dry_run:
        print("\nDRY-RUN complete; no changes written. Re-run without --dry-run to apply.")
    else:
        print("\nMigration complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
