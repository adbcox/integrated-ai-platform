"""NetBox ingester — services + devices + entity_links.

Walks `dcim.devices` and `ipam.services` via pynetbox, populating the
xindex `nodes` and `services` tables and emitting entity_links for
NetBox-known relationships:

    service depends_on service     — from custom_field service_dependencies
    service hosted_on  node        — from ipam.service.device

Doctrine: NEVER raises on NetBox failure. The caller (orchestrator)
inspects the returned summary dict and updates per-source meta. A
failure in this ingester must not affect adr/runbook/register data
or other external sources.

Token comes from the NETBOX_API_TOKEN env var, which the caller is
expected to load from /run/secrets/netbox-credentials.env (rendered
by the vault-agent-xindex sidecar). Token never appears on argv,
stdout, or in summary output.
"""
from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

try:  # pragma: no cover — pynetbox is a runtime dep, optional in unit tests
    import pynetbox  # type: ignore
except ImportError:  # pragma: no cover
    pynetbox = None  # type: ignore


CREDENTIALS_PATH = Path(
    os.environ.get(
        "XINDEX_NETBOX_CREDENTIALS",
        "/run/secrets/netbox-credentials.env",
    )
)


@dataclass
class NetboxIngestResult:
    ok: bool
    services: int = 0
    nodes: int = 0
    entity_links: int = 0
    error: str = ""
    skipped: bool = False
    skip_reason: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "services": self.services,
            "nodes": self.nodes,
            "entity_links": self.entity_links,
            "error": self.error,
            "skipped": self.skipped,
            "skip_reason": self.skip_reason,
        }


def _read_token() -> str | None:
    """Read NETBOX_API_TOKEN from the vault-agent-rendered env file.

    Falls back to the env var directly (useful for tests or operator
    invocation outside the container). Returns None if neither
    source provides a value.
    """
    env = os.environ.get("NETBOX_API_TOKEN")
    if env:
        return env
    if not CREDENTIALS_PATH.is_file():
        return None
    try:
        for line in CREDENTIALS_PATH.read_text().splitlines():
            if "=" not in line:
                continue
            k, v = line.split("=", 1)
            if k.strip() == "NETBOX_API_TOKEN":
                return v.strip()
    except OSError:
        return None
    return None


def _netbox_url() -> str:
    return os.environ.get("NETBOX_URL", "http://host.docker.internal:8084")


def _safe_str(v: Any) -> str:
    if v is None:
        return ""
    return str(v)


def _safe_int(v: Any) -> int | None:
    if v is None:
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _device_name(obj: Any) -> str | None:
    if obj is None:
        return None
    name = getattr(obj, "name", None)
    return str(name) if name else None


def _service_parent(svc: Any) -> tuple[str | None, str | None]:
    """Return (kind, ref) where kind in {'device','virtual_machine',None}."""
    dev = getattr(svc, "device", None)
    if dev is not None:
        return ("device", _device_name(dev))
    vm = getattr(svc, "virtual_machine", None)
    if vm is not None:
        return ("virtual_machine", _device_name(vm))
    return (None, None)


def _custom_fields(obj: Any) -> dict[str, Any]:
    cf = getattr(obj, "custom_fields", None) or {}
    if isinstance(cf, dict):
        return cf
    try:
        return dict(cf)
    except (TypeError, ValueError):
        return {}


def _service_body(svc_row: dict[str, Any]) -> str:
    """Build the FTS body — name + protocol + ports + parent + description + custom keys."""
    parts: list[str] = [svc_row["name"]]
    if svc_row.get("protocol"):
        parts.append(str(svc_row["protocol"]))
    ports = svc_row.get("ports") or []
    if ports:
        parts.append(" ".join(str(p) for p in ports))
    if svc_row.get("parent_ref"):
        parts.append(f"{svc_row['parent_kind']}:{svc_row['parent_ref']}")
    if svc_row.get("description"):
        parts.append(svc_row["description"])
    custom = svc_row.get("custom") or {}
    if isinstance(custom, dict):
        for k, v in custom.items():
            if v in (None, "", [], {}):
                continue
            parts.append(f"{k}={v}")
    return " ".join(parts)


def _node_body(node_row: dict[str, Any]) -> str:
    parts: list[str] = [node_row["name"]]
    for fld in ("role", "site", "status", "primary_ip"):
        if node_row.get(fld):
            parts.append(str(node_row[fld]))
    if node_row.get("description"):
        parts.append(node_row["description"])
    custom = node_row.get("custom") or {}
    if isinstance(custom, dict):
        for k, v in custom.items():
            if v in (None, "", [], {}):
                continue
            parts.append(f"{k}={v}")
    return " ".join(parts)


def _fetch(token: str, url: str) -> tuple[list[Any], list[Any]] | None:
    """Return (devices, services) lists, or None on failure."""
    if pynetbox is None:
        return None
    try:
        api = pynetbox.api(url, token=token)
        devices = list(api.dcim.devices.all())
        services = list(api.ipam.services.all())
        return devices, services
    except Exception:
        return None


def _row_for_node(dev: Any) -> dict[str, Any]:
    primary_ip = getattr(dev, "primary_ip", None)
    return {
        "name": _safe_str(getattr(dev, "name", "")),
        "netbox_id": _safe_int(getattr(dev, "id", None)),
        "role": _safe_str(getattr(getattr(dev, "role", None), "name", "")),
        "site": _safe_str(getattr(getattr(dev, "site", None), "name", "")),
        "status": _safe_str(
            getattr(getattr(dev, "status", None), "value", None)
            or getattr(dev, "status", "")
        ),
        "primary_ip": _safe_str(getattr(primary_ip, "address", "") if primary_ip else ""),
        "description": _safe_str(getattr(dev, "description", "")),
        "custom": _custom_fields(dev),
    }


def _row_for_service(svc: Any) -> dict[str, Any]:
    pkind, pref = _service_parent(svc)
    raw_ports = getattr(svc, "ports", None) or []
    try:
        ports = [int(p) for p in raw_ports]
    except (TypeError, ValueError):
        ports = []
    return {
        "name": _safe_str(getattr(svc, "name", "")),
        "netbox_id": _safe_int(getattr(svc, "id", None)),
        "protocol": _safe_str(
            getattr(getattr(svc, "protocol", None), "value", None)
            or getattr(svc, "protocol", "")
        ),
        "ports": ports,
        "parent_kind": pkind,
        "parent_ref": pref,
        "description": _safe_str(getattr(svc, "description", "")),
        "custom": _custom_fields(svc),
    }


def _service_dependency_targets(custom: dict[str, Any]) -> list[str]:
    """Resolve service_dependencies multi-object field to a list of service names."""
    raw = custom.get("service_dependencies")
    if not raw:
        return []
    out: list[str] = []
    items = raw if isinstance(raw, (list, tuple)) else [raw]
    for it in items:
        # pynetbox returns linked objects with .name; raw API returns dicts.
        name = None
        if hasattr(it, "name"):
            name = getattr(it, "name", None)
        elif isinstance(it, dict):
            name = it.get("name") or it.get("display")
        if name:
            out.append(str(name))
    return out


def _persist(
    conn: sqlite3.Connection,
    devices: list[Any],
    services: list[Any],
) -> tuple[int, int, int]:
    """Write rows + FTS entries + entity_links inside the caller's transaction."""
    nodes_written = 0
    for dev in devices:
        row = _row_for_node(dev)
        if not row["name"]:
            continue
        body = _node_body(row)
        conn.execute(
            """
            INSERT INTO nodes(
                name, netbox_id, role, site, status, primary_ip,
                description, custom_json, source
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, 'netbox')
            ON CONFLICT(name) DO UPDATE SET
                netbox_id=excluded.netbox_id,
                role=excluded.role,
                site=excluded.site,
                status=excluded.status,
                primary_ip=excluded.primary_ip,
                description=excluded.description,
                custom_json=excluded.custom_json,
                source='netbox'
            """,
            (
                row["name"],
                row["netbox_id"],
                row["role"] or None,
                row["site"] or None,
                row["status"] or None,
                row["primary_ip"] or None,
                row["description"],
                json.dumps(row["custom"], default=str, sort_keys=True),
            ),
        )
        conn.execute(
            "INSERT INTO xindex_fts(kind, ref, title, body) VALUES('node', ?, ?, ?)",
            (row["name"], row["name"], body),
        )
        nodes_written += 1

    services_written = 0
    links_written = 0
    for svc in services:
        row = _row_for_service(svc)
        if not row["name"]:
            continue
        body = _service_body(row)
        conn.execute(
            """
            INSERT INTO services(
                name, netbox_id, protocol, ports_json, parent_kind, parent_ref,
                description, custom_json, source
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, 'netbox')
            ON CONFLICT(name) DO UPDATE SET
                netbox_id=excluded.netbox_id,
                protocol=excluded.protocol,
                ports_json=excluded.ports_json,
                parent_kind=excluded.parent_kind,
                parent_ref=excluded.parent_ref,
                description=excluded.description,
                custom_json=excluded.custom_json,
                source='netbox'
            """,
            (
                row["name"],
                row["netbox_id"],
                row["protocol"] or None,
                json.dumps(row["ports"]),
                row["parent_kind"],
                row["parent_ref"],
                row["description"],
                json.dumps(row["custom"], default=str, sort_keys=True),
            ),
        )
        conn.execute(
            "INSERT INTO xindex_fts(kind, ref, title, body) VALUES('service', ?, ?, ?)",
            (row["name"], row["name"], body),
        )
        services_written += 1

        # Entity links — hosted_on (service → device).
        if row["parent_kind"] == "device" and row["parent_ref"]:
            conn.execute(
                """
                INSERT OR IGNORE INTO entity_links(
                    from_kind, from_ref, to_kind, to_ref, link_type, source
                ) VALUES('service', ?, 'node', ?, 'hosted_on', 'netbox')
                """,
                (row["name"], row["parent_ref"]),
            )
            links_written += 1

        # Entity links — depends_on (service → service) from custom field.
        for dep in _service_dependency_targets(row["custom"]):
            if dep == row["name"]:
                continue
            conn.execute(
                """
                INSERT OR IGNORE INTO entity_links(
                    from_kind, from_ref, to_kind, to_ref, link_type, source
                ) VALUES('service', ?, 'service', ?, 'depends_on', 'netbox')
                """,
                (row["name"], dep),
            )
            links_written += 1

    return services_written, nodes_written, links_written


def ingest(
    conn: sqlite3.Connection,
    *,
    fetcher: Any = None,
) -> NetboxIngestResult:
    """Run a NetBox ingest into `conn`.

    Behaviour:
      - if no token available  → skipped (status='error', error='no token')
      - if fetch fails         → error  (status='error'); existing rows
                                  preserved by db.reset_source semantics
                                  (caller wraps this in a transaction)
      - otherwise              → ok, with counts populated.

    `fetcher` is dependency-injectable for tests: it receives
    (token, url) and returns (devices, services) or None on failure.
    """
    token = _read_token()
    if not token:
        return NetboxIngestResult(
            ok=False,
            skipped=True,
            skip_reason="no NETBOX_API_TOKEN available",
            error="no NETBOX_API_TOKEN available",
        )

    fetch = fetcher or _fetch
    try:
        result = fetch(token, _netbox_url())
    except Exception as exc:  # defensive: an injected fetcher shouldn't raise
        return NetboxIngestResult(ok=False, error=f"fetch raised: {exc!r}")

    if result is None:
        return NetboxIngestResult(ok=False, error="netbox unreachable or auth failed")

    devices, services = result

    # Caller has already called db.reset_source(conn, 'netbox') inside
    # the surrounding transaction. We just write.
    try:
        s, n, l = _persist(conn, list(devices), list(services))
    except sqlite3.Error as exc:
        return NetboxIngestResult(ok=False, error=f"sqlite error: {exc!r}")

    return NetboxIngestResult(ok=True, services=s, nodes=n, entity_links=l)
