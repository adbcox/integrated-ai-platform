#!/usr/bin/env python3
"""D-16-02.3 — register xindex-mcp as an ipam.service in NetBox.

Idempotent. Direct sibling of scripts/netbox-register-xindex.py — same
auth path, same diff/upsert logic; only the desired payload differs.

A generalized scripts/netbox-register-service.py (taking name + port +
metadata as args) is a future-work item — see docs/runbooks/xindex-mcp.md
§7. The two near-identical scripts are an intentional intermediate
state: keep the deliverable narrow, surface the abstraction opportunity
once a third service register is needed.

Run from the Mac Mini in the block-4c venv:
    /Users/admin/.venv-block-4c/bin/python scripts/netbox-register-xindex-mcp.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pynetbox  # type: ignore
import requests

NETBOX_URL = os.environ.get("NETBOX_URL", "http://localhost:8084")
CRED_FILE = Path("/Users/admin/.vault-agent-secrets/netbox/credentials.env")
DEVICE_NAME = "mac-mini"
SERVICE_NAME = "xindex-mcp"

DESIRED_CF = {
    "container_name": "xindex-mcp",
    "container_image": "iap/xindex-mcp:0.1.0",
    "compose_file": "docker/xindex-mcp/docker-compose.yml",
    "health_url": "http://127.0.0.1:8096/healthz",
    "health_method": "GET",
    "health_expect": 200,
    "registry_id": "xindex-mcp",
}

# Empty-but-deliberate fields. Comments explain when they will populate.
DESIRED_CF_EMPTY = {
    # No Vault-Agent sidecar: xindex-mcp speaks only to xindex (no
    # external creds). If a future tool needs auth this populates.
    "vault_paths": "",
    "sidecar_of": "",
    "superseded_by": "",
    # Documented dependency: xindex itself. Service-deps is the right
    # place for this; populated below.
    "service_dependencies": [],  # set in code from live xindex service id
    "health_expect_extra": "",
    "public_values": "",
    "security_profile": "",
    # Loopback bind 8096:8096 — operator can curl from host.
    "port_is_internal": False,
    "service_notes": "",
}


def load_token() -> str:
    if not CRED_FILE.is_file():
        sys.exit(f"ERROR: credentials file {CRED_FILE} missing")
    fields: dict[str, str] = {}
    for line in CRED_FILE.read_text().splitlines():
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        fields[k.strip()] = v.strip()
    if "NETBOX_API_TOKEN" not in fields:
        sys.exit("ERROR: NETBOX_API_TOKEN missing from credentials.env")
    return fields["NETBOX_API_TOKEN"]


def main() -> int:
    nb = pynetbox.api(NETBOX_URL, token=load_token())
    nb.http_session = requests.Session()
    print(f"NetBox: {NETBOX_URL}  status={nb.status()['netbox-version']}")

    device = nb.dcim.devices.get(name=DEVICE_NAME)
    if device is None:
        sys.exit(f"ERROR: device {DEVICE_NAME!r} not found in NetBox")

    cc_tag = nb.extras.tags.get(slug="control-center")
    if cc_tag is None:
        sys.exit("ERROR: tag 'control-center' missing")

    # service_dependencies → xindex (we wrap its API)
    xindex_svc = nb.ipam.services.get(name="xindex")
    deps_ids = [xindex_svc.id] if xindex_svc else []
    if not xindex_svc:
        print("WARN: ipam.service 'xindex' not found — leaving service_dependencies empty")

    cf = {**DESIRED_CF, **DESIRED_CF_EMPTY, "service_dependencies": deps_ids}

    desired_payload = {
        "name": SERVICE_NAME,
        "parent_object_type": "dcim.device",
        "parent_object_id": device.id,
        "ports": [8096],
        "protocol": "tcp",
        "description": "MCP wrapper for xindex (D-16-02.3) — read-only agent surface",
        "tags": [cc_tag.id],
        "custom_fields": cf,
    }

    existing = nb.ipam.services.get(name=SERVICE_NAME)
    if existing is None:
        created = nb.ipam.services.create(desired_payload)
        print(f"created  ipam.service id={created.id} name={created.name}")
        return 0

    drift = _diff(existing, desired_payload)
    if not drift:
        print(f"no-op    ipam.service id={existing.id} name={existing.name}")
        return 0
    existing.update(drift)
    print(
        f"updated  ipam.service id={existing.id} name={existing.name} "
        f"changed_keys={sorted(drift.keys())}"
    )
    return 0


def _diff(record, desired: dict) -> dict:
    """Same diff logic as netbox-register-xindex.py — see comments there."""
    live = dict(record)
    drift: dict = {}

    desired_tags = sorted(desired.get("tags", []) or [])
    live_tags = sorted(t["id"] for t in (live.get("tags") or []))
    if desired_tags != live_tags:
        drift["tags"] = desired_tags

    for k, want in desired.items():
        if k == "tags":
            continue
        if k == "parent_object_type":
            if (live.get("parent_object_type") or "") != want:
                drift[k] = want
            continue
        if k == "parent_object_id":
            if (live.get("parent_object_id") or 0) != want:
                drift[k] = want
            continue
        if k == "protocol":
            live_proto = live.get("protocol")
            live_value = live_proto.get("value") if isinstance(live_proto, dict) else live_proto
            if (live_value or "") != want:
                drift[k] = want
            continue
        if k == "custom_fields":
            cf_drift: dict = {}
            live_cf = live.get("custom_fields") or {}
            for ck, cv in want.items():
                lv = live_cf.get(ck)
                if cv == [] and lv is None:
                    continue
                if cv == "" and lv is None:
                    continue
                # Multi-object CF (e.g. service_dependencies) round-trips
                # as [{id, ...}, ...]; we sent [id, ...]. Compare as id sets.
                if (isinstance(cv, list) and isinstance(lv, list)
                        and lv and isinstance(lv[0], dict) and "id" in lv[0]):
                    if sorted(cv) == sorted(item["id"] for item in lv):
                        continue
                if cv != lv:
                    cf_drift[ck] = cv
            if cf_drift:
                drift["custom_fields"] = cf_drift
            continue
        if live.get(k) != want:
            drift[k] = want

    return drift


if __name__ == "__main__":
    sys.exit(main())
