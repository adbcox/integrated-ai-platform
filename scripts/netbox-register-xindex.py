#!/usr/bin/env python3
"""D-16-02.0.5 — register xindex as an ipam.service in NetBox.

Idempotent: looks up the service by `name="xindex"`. Updates in place
if it exists; creates if missing. Re-runs are no-ops once the record
matches the desired state.

Reads the API token from the Vault-Agent-rendered credentials file at
/Users/admin/.vault-agent-secrets/netbox/credentials.env. Same source
as scripts/netbox-custom-fields.py.

Run from the Mac Mini in the block-4c venv:
    /Users/admin/.venv-block-4c/bin/python scripts/netbox-register-xindex.py

Custom fields populated where applicable. Fields left empty (with
reasons) are listed in DESIRED_CF_EMPTY below — those will fill in as
later sub-deliverables (D-16-02.1+) bring xindex's external surface up.
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
SERVICE_NAME = "xindex"

DESIRED_CF = {
    "container_name": "xindex",
    "container_image": "iap/xindex:0.1.0",
    "compose_file": "docker/xindex/docker-compose.yml",
    "health_url": "http://127.0.0.1:8095/healthz",
    "health_method": "GET",
    "health_expect": 200,
    "registry_id": "xindex",
}

# Fields kept empty by deliberate decision in D-16-02.0.5; comments
# explain when they are expected to populate.
DESIRED_CF_EMPTY = {
    # No Vault-Agent sidecar yet — service has no auth and no creds.
    # Will populate when D-16-02.1 adds NetBox ingestion (needs token).
    "vault_paths": "",
    # Not a sidecar; not superseding anything.
    "sidecar_of": "",
    "superseded_by": "",
    # No upstream service deps in the foundation; ingestion is filesystem-only.
    "service_dependencies": [],
    # Not a sealed-vault style service; no extra accepted codes.
    "health_expect_extra": "",
    # No public values to expose; nothing to print on the homepage tile yet.
    "public_values": "",
    # Default security profile is documented in compose; no per-service override.
    "security_profile": "",
    # Loopback host port is bound (8095:8000) so the port is operator-reachable.
    "port_is_internal": False,
    # Free-text running notes — left empty; runbook is the canonical text.
    "service_notes": "",
}


def load_token() -> str:
    if not CRED_FILE.is_file():
        sys.exit(f"ERROR: credentials file {CRED_FILE} missing — is the vault-agent sidecar running?")
    fields: dict[str, str] = {}
    for line in CRED_FILE.read_text().splitlines():
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        fields[k.strip()] = v.strip()
    if "NETBOX_API_TOKEN" not in fields:
        sys.exit("ERROR: NETBOX_API_TOKEN missing from credentials.env — re-render the Vault Agent sidecar")
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
        sys.exit("ERROR: tag 'control-center' missing — run scripts/netbox-custom-fields.py first")

    # NetBox 4.5+ uses a generic FK (parent_object_type / parent_object_id)
    # rather than the legacy `device` / `virtual_machine` fields. Match the
    # shape of existing services on this device — see e.g. the `caddy`
    # entry on mac-mini.
    desired_payload = {
        "name": SERVICE_NAME,
        "parent_object_type": "dcim.device",
        "parent_object_id": device.id,
        "ports": [8095],
        "protocol": "tcp",
        "description": "Cross-Index Service (D-16-02 foundation)",
        "tags": [cc_tag.id],
        "custom_fields": {**DESIRED_CF, **DESIRED_CF_EMPTY},
    }

    existing = nb.ipam.services.get(name=SERVICE_NAME)
    if existing is None:
        created = nb.ipam.services.create(desired_payload)
        print(f"created  ipam.service id={created.id} name={created.name}")
        return 0

    # Idempotent update: compute a normalized diff against the live
    # record and send a PATCH only when something actually differs.
    # pynetbox's built-in `.update()` flags spurious diffs on this
    # endpoint in NetBox 4.5 because tags round-trip as full objects
    # and `service_dependencies` empty-list normalises to None.
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
    """Return only the desired-payload keys that disagree with the record.

    Normalises pynetbox response shapes that don't byte-match the input:
        - tags: live record returns [{id, ...}, ...]; we sent [id, ...]
        - multi-object custom fields: empty list round-trips to None
    """
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
            # NetBox returns {"value": "tcp", "label": "TCP"}; input is "tcp".
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
