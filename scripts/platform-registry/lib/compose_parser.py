"""Compose-file → intent-layer service records.

Reads docker-compose YAML files from the platform's two parent
directories and emits a list of partial service records carrying the
INTENT layer of the registry (per Service Registry MVP spec §4.1).

Runtime state (docker_inspector) and external routing (caddy_reader)
are merged in later by the pipeline.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import yaml

STACK_ROOTS = (
    Path("/Users/admin/control-center-stack/stacks"),
    Path("/Users/admin/repos/integrated-ai-platform/docker"),
)
TOP_LEVEL_FILE = Path("/Users/admin/repos/integrated-ai-platform/docker-compose.yml")
RETIRED_MARKERS = ("_retired", ".parked.yml")


@dataclass
class ComposeServiceRecord:
    service_id: str
    container_name: str
    stack: str
    compose_file: str
    image: str | None
    expose_ports: list[int] = field(default_factory=list)
    host_port_mappings: list[dict] = field(default_factory=list)
    networks: list[str] = field(default_factory=list)
    volumes: list[str] = field(default_factory=list)
    env_var_refs: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)
    parse_errors: list[str] = field(default_factory=list)


def discover_compose_files() -> list[Path]:
    """Return active in-scope compose files (skip _retired/ and .parked.yml)."""
    found: list[Path] = []
    for root in STACK_ROOTS:
        if not root.exists():
            continue
        for p in root.rglob("docker-compose*.y*ml"):
            if any(marker in str(p) for marker in RETIRED_MARKERS):
                continue
            found.append(p)
    if TOP_LEVEL_FILE.exists():
        found.append(TOP_LEVEL_FILE)
    return sorted(set(found))


def _stack_name(compose_path: Path) -> str:
    """Best-effort stack name from path. parent dirname OR file stem."""
    parent = compose_path.parent.name
    if parent in ("docker", "stacks"):
        # top-level compose under docker/ or repo root — use file stem
        return compose_path.stem.replace("docker-compose", "").strip("-") or "root"
    return parent


_PORT_MAP_RE = re.compile(
    r"^(?:(?P<host_ip>[\d.]+):)?(?P<host_port>\d+):(?P<container_port>\d+)(?:/(?P<proto>tcp|udp))?$"
)
_EXPOSE_RE = re.compile(r"^(?P<port>\d+)(?:/(?P<proto>tcp|udp))?$")
_ENV_REF_RE = re.compile(r"\$\{?([A-Z_][A-Z0-9_]*)\}?")


def _parse_port_mapping(item: Any) -> dict | None:
    """Parse a compose `ports:` entry. Returns dict or None if unparseable."""
    if isinstance(item, dict):
        # long form
        host_port = item.get("published")
        container_port = item.get("target")
        proto = item.get("protocol", "tcp")
        host_ip = item.get("host_ip")
        if container_port is None:
            return None
        return {
            "host_ip": host_ip,
            "host_port": int(host_port) if host_port is not None else None,
            "container_port": int(container_port),
            "protocol": proto,
        }
    if isinstance(item, (str, int)):
        s = str(item)
        m = _PORT_MAP_RE.match(s)
        if m:
            return {
                "host_ip": m.group("host_ip"),
                "host_port": int(m.group("host_port")),
                "container_port": int(m.group("container_port")),
                "protocol": m.group("proto") or "tcp",
            }
        # bare "8080" — container-only
        m2 = _EXPOSE_RE.match(s)
        if m2:
            return {
                "host_ip": None,
                "host_port": None,
                "container_port": int(m2.group("port")),
                "protocol": m2.group("proto") or "tcp",
            }
    return None


def _parse_expose(items: Iterable[Any]) -> list[int]:
    out: list[int] = []
    for item in items:
        s = str(item)
        m = _EXPOSE_RE.match(s)
        if m:
            out.append(int(m.group("port")))
    return out


def _parse_networks(spec: Any) -> list[str]:
    if spec is None:
        return []
    if isinstance(spec, list):
        return [str(x) for x in spec]
    if isinstance(spec, dict):
        return sorted(spec.keys())
    return []


def _parse_volumes(spec: Any) -> list[str]:
    if not spec:
        return []
    out: list[str] = []
    for item in spec:
        if isinstance(item, dict):
            src = item.get("source", "")
            tgt = item.get("target", "")
            out.append(f"{src}:{tgt}".strip(":"))
        else:
            out.append(str(item))
    return out


def _parse_env_refs(svc: dict) -> list[str]:
    """Extract env var NAMES referenced in this service (no values)."""
    refs: set[str] = set()
    env = svc.get("environment")
    if isinstance(env, dict):
        for k, v in env.items():
            refs.add(str(k))
            if isinstance(v, str):
                for m in _ENV_REF_RE.finditer(v):
                    refs.add(m.group(1))
    elif isinstance(env, list):
        for item in env:
            if isinstance(item, str):
                if "=" in item:
                    refs.add(item.split("=", 1)[0])
                else:
                    refs.add(item)
                for m in _ENV_REF_RE.finditer(item):
                    refs.add(m.group(1))
    # also scan command + entrypoint strings
    for key in ("command", "entrypoint"):
        v = svc.get(key)
        if isinstance(v, str):
            for m in _ENV_REF_RE.finditer(v):
                refs.add(m.group(1))
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, str):
                    for m in _ENV_REF_RE.finditer(item):
                        refs.add(m.group(1))
    return sorted(refs)


def _parse_depends_on(spec: Any) -> list[str]:
    if not spec:
        return []
    if isinstance(spec, list):
        return sorted(str(x) for x in spec)
    if isinstance(spec, dict):
        return sorted(spec.keys())
    return []


def parse_compose_file(path: Path) -> list[ComposeServiceRecord]:
    """Return one ComposeServiceRecord per service in this file."""
    out: list[ComposeServiceRecord] = []
    try:
        with open(path) as f:
            data = yaml.safe_load(f)
    except Exception as e:
        # synthesize a single error record so failure is visible
        out.append(
            ComposeServiceRecord(
                service_id=f"PARSE_FAIL:{path.name}",
                container_name="",
                stack=_stack_name(path),
                compose_file=str(path),
                image=None,
                parse_errors=[f"yaml load: {type(e).__name__}: {e}"],
            )
        )
        return out
    if not isinstance(data, dict):
        return out
    services = data.get("services") or {}
    if not isinstance(services, dict):
        return out
    stack = _stack_name(path)
    for svc_key, svc in services.items():
        if not isinstance(svc, dict):
            continue
        rec = ComposeServiceRecord(
            service_id=svc.get("container_name") or svc_key,
            container_name=svc.get("container_name") or svc_key,
            stack=stack,
            compose_file=str(path),
            image=svc.get("image"),
        )
        # ports
        for p in svc.get("ports", []) or []:
            mapping = _parse_port_mapping(p)
            if mapping:
                rec.host_port_mappings.append(mapping)
            else:
                rec.parse_errors.append(f"unparseable ports entry: {p!r}")
        # expose
        rec.expose_ports = _parse_expose(svc.get("expose", []) or [])
        # networks
        rec.networks = _parse_networks(svc.get("networks"))
        # volumes
        rec.volumes = _parse_volumes(svc.get("volumes"))
        # env refs
        rec.env_var_refs = _parse_env_refs(svc)
        # depends_on
        rec.depends_on = _parse_depends_on(svc.get("depends_on"))
        out.append(rec)
    return out


def parse_all() -> list[ComposeServiceRecord]:
    """Discover + parse every in-scope compose file."""
    records: list[ComposeServiceRecord] = []
    for path in discover_compose_files():
        records.extend(parse_compose_file(path))
    return records


if __name__ == "__main__":  # smoke
    recs = parse_all()
    ok = [r for r in recs if not r.service_id.startswith("PARSE_FAIL:")]
    fail = [r for r in recs if r.service_id.startswith("PARSE_FAIL:")]
    print(f"records: {len(recs)}  ok: {len(ok)}  parse-fails: {len(fail)}")
    print(f"sample (first 5):")
    for r in ok[:5]:
        print(
            f"  {r.service_id:30s} stack={r.stack:20s} "
            f"image={(r.image or '<none>')[:40]} "
            f"ports={len(r.host_port_mappings)} expose={r.expose_ports} "
            f"deps={r.depends_on}"
        )
