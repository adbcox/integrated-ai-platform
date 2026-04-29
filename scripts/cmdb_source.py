#!/usr/bin/env python3
"""CMDB source loader — registry YAML or NetBox.

Block 4.C C5.2 — additive NetBox path alongside the legacy YAML reader.
Both backends emit the same list-of-services schema so downstream
consumers (validate-cmdb.sh, topology-api, control-plane registry) can
swap source without changing their validation/render logic.

Usage:
    CMDB_SOURCE=yaml   python3 scripts/cmdb_source.py
    CMDB_SOURCE=netbox python3 scripts/cmdb_source.py

    # Library use:
    from cmdb_source import load_services
    services = load_services()  # respects $CMDB_SOURCE; defaults to yaml

Env vars:
    CMDB_SOURCE        yaml | netbox  (default: yaml)
    CMDB_REGISTRY      override path to the deprecated registry YAML
                       (default: config/service-registry.yaml.DEPRECATED)
    NETBOX_URL         default http://localhost:8084
    NETBOX_API_TOKEN   V2 token (nbt_<key>.<secret>)
                       falls back to /Users/admin/.vault-agent-secrets/netbox/credentials.env

Equivalence guarantee:
    The two backends emit byte-identical JSON when sorted/normalized
    (see scripts/cmdb-equivalence.sh). Differences in source order are
    not equivalence failures; differences in any field value are.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = REPO_ROOT / "config" / "service-registry.yaml.DEPRECATED"
DEFAULT_NETBOX_URL = "http://localhost:8084"
# Vault-Agent rendered token file. Default is the host path; containers
# (topology-api, control-plane) override via NETBOX_CREDENTIALS_FILE env
# to point at their bind-mounted view.
NETBOX_VAULT_ENV = Path(
    os.environ.get(
        "NETBOX_CREDENTIALS_FILE",
        "/Users/admin/.vault-agent-secrets/netbox/credentials.env",
    )
)

# Tags that are NOT categories — they describe kind or lifecycle.
NON_CATEGORY_TAGS = {"sidecar", "support-service", "deprecated"}

# Sentinel port for port-less services (workers, housekeeping). C3
# Discovery #12 chose port 1 because NetBox requires non-empty `ports`
# but registry YAML allows null. When emitting YAML-equivalent output
# from NetBox, port=1 must be re-emitted as null on services whose
# registry counterpart had no port.
SENTINEL_PORT = 1


# ── YAML backend ──────────────────────────────────────────────────────


def _load_yaml(path: Path) -> list[dict]:
    import yaml  # local import; only the YAML backend needs pyyaml
    with path.open() as f:
        reg = yaml.safe_load(f)
    if "services" not in reg:
        raise SystemExit(f"ERROR: no 'services' key in {path}")
    services = list(reg["services"])
    # Dedup by id, last-wins. Matches C3 migration semantics
    # (Discovery #9 / C1 audit option 1). Any drift from this rule
    # would silently break NetBox equivalence.
    seen: dict[str, dict] = {}
    for s in services:
        sid = s.get("id")
        if not sid:
            continue
        seen[sid] = s
    out = list(seen.values())
    # Normalize cosmetic shape so YAML and NetBox loaders emit
    # comparable structures (no semantic change to YAML data):
    #   - credentials_env: collapse `credentials` and `credentials_env`
    #     into one combined list (mirrors NetBox `vault_paths` field)
    #   - deprecated: explicit bool (NetBox stores via tag presence)
    #   - health_method: default "GET" (NetBox defaults same)
    for s in out:
        creds_env = s.get("credentials_env") or []
        creds = s.get("credentials") or []
        if isinstance(creds, str):
            creds = [creds] if creds.lower() != "none" else []
        if creds_env or creds:
            s["credentials_env"] = list(creds_env) + list(creds)
        s.pop("credentials", None)
        s["deprecated"] = bool(s.get("deprecated"))
        if not s.get("health_method"):
            s["health_method"] = "GET"
        # Drop internal_port when it equals port (redundant) — NetBox
        # only stores `internal_port` when host-port is null, so YAML
        # should match that semantic to round-trip cleanly.
        if s.get("internal_port") is not None and s.get("internal_port") == s.get("port"):
            s.pop("internal_port", None)
    return out


# ── NetBox backend ────────────────────────────────────────────────────


def _read_netbox_token() -> str:
    tok = os.environ.get("NETBOX_API_TOKEN")
    if tok:
        return tok
    if NETBOX_VAULT_ENV.is_file():
        for line in NETBOX_VAULT_ENV.read_text().splitlines():
            if line.startswith("NETBOX_API_TOKEN="):
                return line.split("=", 1)[1].strip()
    raise SystemExit(
        "ERROR: no NETBOX_API_TOKEN in env or "
        f"{NETBOX_VAULT_ENV} (Vault Agent rendered file)"
    )


def _netbox_get(url: str, token: str) -> dict:
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:300]
        raise SystemExit(f"ERROR: NetBox {e.code} on {url}\n  body: {body}")
    except Exception as e:
        raise SystemExit(f"ERROR: NetBox unreachable at {url}: {e}")


def _load_netbox_services(base_url: str, token: str) -> list[dict]:
    """Pull all ipam.service objects across pages, plus the parent device map."""
    # Devices: lets us resolve parent_object_id → host name.
    devices: dict[int, str] = {}
    url = f"{base_url}/api/dcim/devices/?limit=200"
    while url:
        page = _netbox_get(url, token)
        for d in page["results"]:
            devices[d["id"]] = d["name"]
        url = page.get("next")

    # Services
    services: list[dict] = []
    url = f"{base_url}/api/ipam/services/?limit=200"
    while url:
        page = _netbox_get(url, token)
        services.extend(page["results"])
        url = page.get("next")

    # Build id → registry_id map for resolving service_dependencies
    svc_id_to_regid: dict[int, str] = {}
    for s in services:
        cf = s.get("custom_fields") or {}
        rid = cf.get("registry_id") or s["name"]
        svc_id_to_regid[s["id"]] = rid

    out: list[dict] = []
    for s in services:
        cf = s.get("custom_fields") or {}
        host = devices.get(s.get("parent_object_id") or 0, "")
        # Tags: split into category, kind, lifecycle
        tag_names = [t["name"] for t in s.get("tags", [])]
        category = next((t for t in tag_names if t not in NON_CATEGORY_TAGS), "")
        kind = next((t for t in tag_names if t in {"sidecar", "support-service"}), None)
        deprecated = "deprecated" in tag_names

        # ports: re-emit sentinel as None and re-emit
        # internal-only ports as None on `port` (registry semantics:
        # `port=null, internal_port=N`). The C5.2 schema fix added
        # `port_is_internal` so NetBox can round-trip this distinction
        # — see Discovery #17 in the C2 discoveries doc.
        ports = s.get("ports") or []
        port: int | None = None
        internal_port: int | None = None
        if ports:
            raw = ports[0]
            if raw == SENTINEL_PORT:
                port = None  # port-less worker
            elif cf.get("port_is_internal"):
                port = None
                internal_port = raw
            else:
                port = raw

        # depends_on: NetBox returns expanded objects in service_dependencies
        deps_raw = cf.get("service_dependencies") or []
        depends_on: list[str] = []
        for d in deps_raw:
            # In list endpoint the value is a list of {id,url,display}
            did = d.get("id") if isinstance(d, dict) else d
            if did in svc_id_to_regid:
                depends_on.append(svc_id_to_regid[did])

        # security: deserialize the JSON string custom field
        sec_raw = cf.get("security_profile") or ""
        security: dict = {}
        if sec_raw:
            try:
                security = json.loads(sec_raw)
            except Exception:
                security = {}

        # public_values: same JSON-string treatment
        pv_raw = cf.get("public_values") or ""
        public_values: dict = {}
        if pv_raw:
            try:
                public_values = json.loads(pv_raw)
            except Exception:
                public_values = {}

        # vault_paths: registry stores it as either credentials_env
        # (list of env-var names) or credentials (list of vault paths).
        # The migration script joined them with newlines into one
        # field. Equivalence needs us to round-trip them as a
        # combined list — no way to know which side they came from
        # so we treat the whole thing as `credentials_env` for
        # equivalence purposes. validate-cmdb.sh and topology-api
        # do not consume credentials/credentials_env so this is a
        # round-trip artifact, not a behavioural divergence. Surfaced
        # in equivalence diff as field "vault_paths_combined".
        vault_paths_combined = [
            x for x in (cf.get("vault_paths") or "").splitlines() if x.strip()
        ]

        # health_expect: NetBox stores int; 0 means "absent in registry"
        # (registry default also 200). Re-emit as 200 for absent.
        # Multi-value lists ([200, 302]) round-trip via
        # health_expect_extra (added at C5.2; Discovery #17).
        he_primary = cf.get("health_expect") or 0
        he_extra_raw = (cf.get("health_expect_extra") or "").strip()
        he_extra: list[int] = []
        if he_extra_raw:
            for tok in he_extra_raw.split(","):
                tok = tok.strip()
                if tok:
                    try:
                        he_extra.append(int(tok))
                    except ValueError:
                        pass
        if he_extra:
            health_expect: int | list[int] = [he_primary or 200, *he_extra]
        else:
            health_expect = he_primary if he_primary else 200

        notes = cf.get("service_notes") or ""

        # purpose: recover from `comments` by stripping the trailing
        # service_notes block. Migration script wrote
        #   comments = purpose [+ "\n\n" + notes]
        # so reverse-split on the notes tail. When migration spec
        # had no purpose, comments == notes (unsplittable; treat as
        # purpose-empty). See scripts/migrate-registry-to-netbox.py
        # build_service_payload().
        comments = (s.get("comments") or "").strip()
        purpose = ""
        if comments:
            if notes and comments.endswith(notes.strip()):
                purpose = comments[: -len(notes.strip())].rstrip()
                # The "\n\n" separator may also need stripping
                if purpose.endswith("\n\n"):
                    purpose = purpose[:-2].rstrip()
            elif not notes:
                purpose = comments

        # registry_id is the canonical "id" key in registry YAML
        rid = cf.get("registry_id") or s["name"]

        rec = {
            "id": rid,
            "name": s.get("description") or s["name"],
            "category": category,
            "host": host,
            "container": cf.get("container_name") or "",
            "image": cf.get("container_image") or "",
            "port": port,
            "internal_port": internal_port,
            "health_url": cf.get("health_url") or "",
            "health_method": cf.get("health_method") or "GET",
            "health_expect": health_expect,
            "depends_on": sorted(depends_on),
            "security": security,
            "compose_file": cf.get("compose_file") or "",
            "credentials_env": vault_paths_combined,
            "public_values": public_values,
            "notes": notes,
            "purpose": purpose,
            "sidecar_of": cf.get("sidecar_of") or None,
            "superseded_by": cf.get("superseded_by") or None,
            "kind": kind,
            "deprecated": deprecated,
        }
        # Drop empty / None-equivalent keys that the YAML side wouldn't carry
        rec = {k: v for k, v in rec.items() if v not in (None, "", [], {})}
        out.append(rec)
    return out


# ── Public entrypoints ────────────────────────────────────────────────


def load_services() -> list[dict]:
    src = os.environ.get("CMDB_SOURCE", "yaml").lower()
    if src == "yaml":
        path = Path(os.environ.get("CMDB_REGISTRY") or DEFAULT_REGISTRY)
        return _load_yaml(path)
    if src == "netbox":
        url = os.environ.get("NETBOX_URL", DEFAULT_NETBOX_URL).rstrip("/")
        return _load_netbox_services(url, _read_netbox_token())
    raise SystemExit(f"ERROR: unknown CMDB_SOURCE={src!r} (expected yaml|netbox)")


def main() -> int:
    services = load_services()
    json.dump(services, sys.stdout)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
