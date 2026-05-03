"""Docker runtime state → reality-layer service records.

Per Service Registry MVP spec §4.2. Calls `docker inspect` for every
running container and produces records that can be merged with the
intent-layer records emitted by compose_parser.

Failure modes handled:
  - docker daemon unreachable → return empty list, mark error
  - container in compose but not running → intent record passes
    through unmerged (state.status = "absent")
  - container running but not in compose → emit a record with
    stack="<orphan>", surface in metadata
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from typing import Any


@dataclass
class DockerRuntimeRecord:
    container_name: str
    container_id: str
    state_status: str  # "running" | "exited" | "restarting" | "paused" | "dead"
    health_status: str | None  # "healthy" | "unhealthy" | "starting" | None
    started_at: str | None
    restart_count: int
    image: str | None
    actual_port_bindings: list[dict] = field(default_factory=list)
    actual_networks: list[dict] = field(default_factory=list)
    actual_mounts: list[dict] = field(default_factory=list)
    restart_policy: str | None = None
    inspect_errors: list[str] = field(default_factory=list)


def _run(cmd: list[str], timeout: int = 20) -> tuple[int, str, str]:
    try:
        r = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, check=False
        )
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"timeout after {timeout}s"
    except FileNotFoundError as e:
        return -2, "", f"docker not found: {e}"


def list_all_containers() -> list[str]:
    """Return container IDs for ALL containers (running + stopped)."""
    rc, out, err = _run(["docker", "ps", "-a", "-q", "--no-trunc"])
    if rc != 0:
        return []
    return [line.strip() for line in out.splitlines() if line.strip()]


def inspect_container(cid: str) -> dict | None:
    rc, out, err = _run(["docker", "inspect", cid])
    if rc != 0:
        return None
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return None
    if not data:
        return None
    return data[0]


def _parse_port_bindings(network_settings: dict) -> list[dict]:
    """Convert NetworkSettings.Ports → list of bindings."""
    out: list[dict] = []
    ports = network_settings.get("Ports") or {}
    for container_port_proto, host_bindings in ports.items():
        # container_port_proto looks like "8080/tcp"
        if "/" in container_port_proto:
            cp_str, proto = container_port_proto.split("/", 1)
        else:
            cp_str, proto = container_port_proto, "tcp"
        try:
            cp = int(cp_str)
        except ValueError:
            continue
        if not host_bindings:
            # exposed but unbound on host
            out.append(
                {
                    "container_port": cp,
                    "protocol": proto,
                    "host_ip": None,
                    "host_port": None,
                }
            )
        else:
            for hb in host_bindings:
                try:
                    hp = int(hb.get("HostPort", "")) if hb.get("HostPort") else None
                except ValueError:
                    hp = None
                out.append(
                    {
                        "container_port": cp,
                        "protocol": proto,
                        "host_ip": hb.get("HostIp") or None,
                        "host_port": hp,
                    }
                )
    return out


def _parse_networks(network_settings: dict) -> list[dict]:
    out: list[dict] = []
    nets = network_settings.get("Networks") or {}
    for name, n in nets.items():
        out.append(
            {
                "network": name,
                "ip": n.get("IPAddress") or None,
                "gateway": n.get("Gateway") or None,
                "aliases": n.get("Aliases") or [],
            }
        )
    return out


def _parse_mounts(mounts: list[dict]) -> list[dict]:
    out: list[dict] = []
    for m in mounts or []:
        out.append(
            {
                "type": m.get("Type"),
                "source": m.get("Source"),
                "target": m.get("Destination"),
                "mode": m.get("Mode"),
                "rw": m.get("RW"),
            }
        )
    return out


def to_record(inspect_data: dict) -> DockerRuntimeRecord:
    name = (inspect_data.get("Name") or "").lstrip("/")
    state = inspect_data.get("State") or {}
    health = (state.get("Health") or {}).get("Status")
    cfg = inspect_data.get("Config") or {}
    host_cfg = inspect_data.get("HostConfig") or {}
    net_settings = inspect_data.get("NetworkSettings") or {}
    rec = DockerRuntimeRecord(
        container_name=name,
        container_id=(inspect_data.get("Id") or "")[:12],
        state_status=(state.get("Status") or "").lower(),
        health_status=health,
        started_at=state.get("StartedAt"),
        restart_count=int(state.get("RestartCount") or 0),
        image=cfg.get("Image"),
        actual_port_bindings=_parse_port_bindings(net_settings),
        actual_networks=_parse_networks(net_settings),
        actual_mounts=_parse_mounts(inspect_data.get("Mounts")),
        restart_policy=(host_cfg.get("RestartPolicy") or {}).get("Name"),
    )
    return rec


def inspect_all() -> tuple[list[DockerRuntimeRecord], list[str]]:
    """Inspect every container; return (records, error-messages)."""
    errors: list[str] = []
    cids = list_all_containers()
    if not cids:
        rc, _, err = _run(["docker", "info"])
        if rc != 0:
            errors.append(f"docker info failed: {err.strip()[:200]}")
        return [], errors
    out: list[DockerRuntimeRecord] = []
    for cid in cids:
        data = inspect_container(cid)
        if not data:
            errors.append(f"inspect failed for {cid[:12]}")
            continue
        try:
            out.append(to_record(data))
        except Exception as e:
            errors.append(f"to_record failed for {cid[:12]}: {type(e).__name__}: {e}")
    return out, errors


def merge_with_compose(
    intent_records: list, runtime_records: list[DockerRuntimeRecord]
) -> tuple[list[dict], list[dict], list[str]]:
    """Merge intent-layer (compose) with reality-layer (docker inspect).

    Returns (merged_records, orphan_runtime_records, warnings).
    Each merged record is the dict-form of the spec §5 schema, with
    state + addresses.internal + addresses.host_mapped populated from
    runtime_records when matched by container_name.
    """
    runtime_by_name: dict[str, DockerRuntimeRecord] = {
        r.container_name: r for r in runtime_records
    }
    matched_runtime_names: set[str] = set()
    merged: list[dict] = []
    warnings: list[str] = []

    for intent in intent_records:
        if intent.service_id.startswith("PARSE_FAIL:"):
            continue
        rt = runtime_by_name.get(intent.container_name)
        rec: dict[str, Any] = {
            "service_id": intent.service_id,
            "container_name": intent.container_name,
            "stack": intent.stack,
            "compose_file": intent.compose_file,
            "image": intent.image,
            "state": {
                "status": "absent",
                "health": None,
                "started_at": None,
                "restart_count": 0,
            },
            "addresses": {
                "internal": [],
                "host_mapped": [],
                "caddy_routes": [],
            },
            "credentials": {},
            "depends_on": list(intent.depends_on),
            "depended_on_by": [],
            "known_failure_modes": [],
            "access_examples": [],
            "documentation_refs": [],
            "_intent": {
                "expose_ports": list(intent.expose_ports),
                "host_port_mappings": list(intent.host_port_mappings),
                "networks": list(intent.networks),
                "volumes": list(intent.volumes),
                "env_var_refs": list(intent.env_var_refs),
            },
            "_warnings": list(intent.parse_errors),
        }
        if rt is not None:
            matched_runtime_names.add(rt.container_name)
            rec["state"] = {
                "status": rt.state_status,
                "health": rt.health_status,
                "started_at": rt.started_at,
                "restart_count": rt.restart_count,
                "restart_policy": rt.restart_policy,
            }
            # internal: per network IP + best-known listen port
            #  (we don't know the listen port from inspect alone; use
            #  intent expose_ports + container-side of host bindings)
            listen_ports: set[int] = set(intent.expose_ports)
            for b in rt.actual_port_bindings:
                listen_ports.add(b["container_port"])
            for net in rt.actual_networks:
                for lp in sorted(listen_ports):
                    rec["addresses"]["internal"].append(
                        {
                            "network": net["network"],
                            "ip": net["ip"],
                            "port_listen": lp,
                            "protocol": "tcp",
                        }
                    )
            # host_mapped from actual bindings only
            rec["addresses"]["host_mapped"] = [
                {
                    "host_ip": b["host_ip"],
                    "host_port": b["host_port"],
                    "container_port": b["container_port"],
                    "protocol": b["protocol"],
                }
                for b in rt.actual_port_bindings
                if b.get("host_port") is not None
            ]
            # image override if runtime differs
            if rt.image and rt.image != intent.image:
                rec["_warnings"].append(
                    f"image drift: compose={intent.image} runtime={rt.image}"
                )
        else:
            rec["_warnings"].append(
                f"defined in compose but not running ({intent.compose_file})"
            )
        merged.append(rec)

    # back-link depended_on_by
    by_name = {r["container_name"]: r for r in merged}
    for r in merged:
        for dep in r["depends_on"]:
            if dep in by_name:
                by_name[dep]["depended_on_by"].append(r["service_id"])

    # orphans — running containers not in any compose
    orphans: list[dict] = []
    for rt in runtime_records:
        if rt.container_name in matched_runtime_names:
            continue
        orphans.append(
            {
                "service_id": rt.container_name,
                "container_name": rt.container_name,
                "stack": "<orphan>",
                "compose_file": None,
                "image": rt.image,
                "state": {
                    "status": rt.state_status,
                    "health": rt.health_status,
                    "started_at": rt.started_at,
                    "restart_count": rt.restart_count,
                    "restart_policy": rt.restart_policy,
                },
                "addresses": {
                    "internal": [
                        {
                            "network": n["network"],
                            "ip": n["ip"],
                            "port_listen": None,
                            "protocol": "tcp",
                        }
                        for n in rt.actual_networks
                    ],
                    "host_mapped": [
                        {
                            "host_ip": b["host_ip"],
                            "host_port": b["host_port"],
                            "container_port": b["container_port"],
                            "protocol": b["protocol"],
                        }
                        for b in rt.actual_port_bindings
                        if b.get("host_port") is not None
                    ],
                    "caddy_routes": [],
                },
                "credentials": {},
                "depends_on": [],
                "depended_on_by": [],
                "known_failure_modes": [],
                "access_examples": [],
                "documentation_refs": [],
                "_warnings": ["running but not declared in any in-scope compose file"],
            }
        )

    return merged, orphans, warnings


if __name__ == "__main__":
    runtime, errs = inspect_all()
    print(f"runtime records: {len(runtime)}  errors: {len(errs)}")
    for e in errs[:5]:
        print(f"  err: {e}")
    if runtime:
        print("sample (first 3):")
        for r in runtime[:3]:
            print(
                f"  {r.container_name:30s} {r.state_status:10s} "
                f"health={r.health_status} bindings={len(r.actual_port_bindings)} "
                f"nets={len(r.actual_networks)}"
            )
