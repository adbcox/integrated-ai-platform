#!/usr/bin/env python3
"""Block 4.C C3.1 — provision NetBox custom fields and tags.

Idempotent: safe to re-run. Looks up existing objects by `name`/`slug`
and updates them in place; only creates if missing.

Reads the API token from the Vault-Agent-rendered credentials file at
/Users/admin/.vault-agent-secrets/netbox/credentials.env. Token never
appears on argv or stdout.

Run from the Mac Mini in the block-4c venv:
    /Users/admin/.venv-block-4c/bin/python scripts/netbox-custom-fields.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pynetbox  # type: ignore
import requests

NETBOX_URL = os.environ.get("NETBOX_URL", "http://localhost:8084")
CRED_FILE = Path("/Users/admin/.vault-agent-secrets/netbox/credentials.env")


def load_token() -> str:
    """Return the full V2 wire token (nbt_<key>.<secret>) for API auth.

    Prefers NETBOX_API_TOKEN (assembled by the Vault Agent template).
    Falls back to SUPERUSER_API_TOKEN for backwards compat — but that
    is only the secret half and will fail against NetBox 4.5+.
    """
    if not CRED_FILE.is_file():
        sys.exit(f"ERROR: credentials file {CRED_FILE} missing — is the vault-agent sidecar running?")
    fields: dict[str, str] = {}
    for line in CRED_FILE.read_text().splitlines():
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        fields[k.strip()] = v.strip()
    if "NETBOX_API_TOKEN" in fields:
        return fields["NETBOX_API_TOKEN"]
    sys.exit("ERROR: NETBOX_API_TOKEN missing from credentials.env — re-render the Vault Agent sidecar after Block 4.C C3 update")


# Custom field definitions. Each entry: (name, label, type, content_types, kwargs).
# content_types is a list of NetBox object types (app.model) the field attaches to.
# Per C1 audit recommendation — `service_dependencies` uses multi-object referencing
# ipam.service for native graph traversal.
CUSTOM_FIELDS = [
    {
        "name": "container_name",
        "label": "Container name",
        "type": "text",
        "object_types": ["ipam.service"],
    },
    {
        "name": "container_image",
        "label": "Container image",
        "type": "text",
        "object_types": ["ipam.service"],
    },
    {
        "name": "health_url",
        "label": "Health-check URL",
        "type": "text",
        "object_types": ["ipam.service"],
    },
    {
        "name": "health_method",
        "label": "Health-check HTTP method",
        "type": "text",
        "object_types": ["ipam.service"],
    },
    {
        "name": "health_expect",
        "label": "Health-check expected status",
        "type": "integer",
        "object_types": ["ipam.service"],
    },
    {
        "name": "compose_file",
        "label": "Compose file path",
        "type": "text",
        "object_types": ["ipam.service"],
    },
    {
        "name": "vault_paths",
        "label": "Vault paths (env + credentials)",
        "type": "longtext",
        "object_types": ["ipam.service"],
    },
    {
        "name": "security_profile",
        "label": "Security profile (JSON)",
        "type": "longtext",
        "object_types": ["ipam.service"],
    },
    {
        "name": "public_values",
        "label": "Public values (JSON)",
        "type": "longtext",
        "object_types": ["ipam.service"],
    },
    {
        "name": "service_notes",
        "label": "Service notes",
        "type": "longtext",
        "object_types": ["ipam.service"],
    },
    {
        "name": "sidecar_of",
        "label": "Sidecar of",
        "type": "text",
        "object_types": ["ipam.service"],
    },
    {
        "name": "superseded_by",
        "label": "Superseded by",
        "type": "text",
        "object_types": ["ipam.service"],
    },
    {
        "name": "registry_id",
        "label": "Registry ID (canonical key)",
        "type": "text",
        "object_types": ["ipam.service"],
    },
    {
        "name": "service_dependencies",
        "label": "Service dependencies",
        "type": "multiobject",
        "object_types": ["ipam.service"],
        "object_type": "ipam.service",
    },
    # Block 4.C C5.2 — round-trip schema additions
    # ─────────────────────────────────────────────
    # The C3 migration was lossy on two dimensions, surfaced at the C5.2
    # equivalence probe and resolved by extending NetBox's schema:
    #
    #  - health_expect_extra (longtext, comma-separated ints):
    #     captures additional acceptable status codes beyond the primary
    #     `health_expect`. Registry YAML allows lists like
    #     [200, 429, 472, 473, 501, 503] (Vault when sealed). C3
    #     collapsed to first; this field carries the rest.
    #
    #  - port_is_internal (boolean):
    #     true when the service uses `internal_port` only and has no
    #     host port binding. C3 stored either `port` or fall-through
    #     `internal_port` in `ipam.service.ports`, losing the bit.
    #     Tells consumers (port-conflict checks, "what's listening")
    #     to filter this service out of host-port-scoped queries.
    {
        "name": "health_expect_extra",
        "label": "Health-check extra accepted codes",
        "type": "longtext",
        "object_types": ["ipam.service"],
    },
    {
        "name": "port_is_internal",
        "label": "Port is container-internal only",
        "type": "boolean",
        "object_types": ["ipam.service"],
    },
]

# Tags created upfront so service objects can reference them by slug.
# Categories observed in the registry as of Block 4.C C1 audit.
CATEGORY_TAGS = [
    "ai", "automation", "cmdb", "control-center", "data", "home-automation",
    "infrastructure", "integration", "mcp", "mcp-shim", "media", "monitoring",
    "network", "observability", "platform", "visibility",
]

KIND_TAGS = ["sidecar", "support-service"]
LIFECYCLE_TAGS = ["deprecated"]


def upsert_custom_field(nb, spec: dict) -> str:
    name = spec["name"]
    existing = nb.extras.custom_fields.get(name=name)
    payload = {
        "name": name,
        "label": spec["label"],
        "type": spec["type"],
        "object_types": spec["object_types"],
        "required": False,
    }
    if "object_type" in spec:
        payload["related_object_type"] = spec["object_type"]
    if existing:
        existing.update(payload)
        return f"updated  custom_field {name}"
    nb.extras.custom_fields.create(payload)
    return f"created  custom_field {name}"


def upsert_tag(nb, name: str, slug: str | None = None, color: str = "9e9e9e") -> str:
    slug = slug or name.lower().replace("_", "-").replace(" ", "-")
    existing = nb.extras.tags.get(slug=slug)
    payload = {"name": name, "slug": slug, "color": color}
    if existing:
        existing.update(payload)
        return f"updated  tag {slug}"
    nb.extras.tags.create(payload)
    return f"created  tag {slug}"


def main() -> int:
    token = load_token()
    sess = requests.Session()
    nb = pynetbox.api(NETBOX_URL, token=token)
    nb.http_session = sess

    print(f"NetBox: {NETBOX_URL}  status={nb.status()['netbox-version']}")

    print("\n── Custom fields ────────────────────────────────────────")
    for spec in CUSTOM_FIELDS:
        print(f"  {upsert_custom_field(nb, spec)}")

    print("\n── Tags: categories ──────────────────────────────────────")
    for name in CATEGORY_TAGS:
        print(f"  {upsert_tag(nb, name=name, color='2196f3')}")

    print("\n── Tags: kinds ───────────────────────────────────────────")
    for name in KIND_TAGS:
        print(f"  {upsert_tag(nb, name=name, color='ff9800')}")

    print("\n── Tags: lifecycle ───────────────────────────────────────")
    for name in LIFECYCLE_TAGS:
        print(f"  {upsert_tag(nb, name=name, color='f44336')}")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
