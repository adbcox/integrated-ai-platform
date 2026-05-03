"""Integration tests for caddy_reader against the live Caddy admin API
+ Caddyfile. These are platform-level tests; if the Caddyfile changes
shape (new sites, removed sites) the count assertions need a refresh.
"""

from __future__ import annotations

import sys
from pathlib import Path

LIB = Path(__file__).resolve().parent.parent / "lib"
sys.path.insert(0, str(LIB))

import caddy_reader as cr  # noqa: E402
import compose_parser as cp  # noqa: E402
import docker_inspector as di  # noqa: E402


def test_admin_api_or_caddyfile_returns_routes():
    routes, src = cr.read_routes()
    assert routes, f"no routes from either source (src={src})"
    assert src in ("admin_api", "caddyfile")


def test_caddyfile_parser_alone_works():
    """Parser must function even if admin API is down."""
    routes = cr.read_caddyfile()
    assert routes, "Caddyfile parser returned 0 routes"
    hosts = {r.external_host for r in routes}
    # spot-check known sites
    for required in ("vault.internal", "grafana.internal", "homeassistant.internal"):
        assert required in hosts, f"{required} missing from Caddyfile parse"


def test_admin_api_route_count_matches_caddyfile_within_tolerance():
    api = cr.read_admin_api()
    fil = cr.read_caddyfile()
    if not api:
        return  # API down — skip; covered by fallback test
    # Admin API expands subroutes; Caddyfile gives one route per site.
    # They should match closely.
    assert abs(len(api) - len(fil)) <= 3, (
        f"large divergence: api={len(api)} caddyfile={len(fil)}"
    )


def test_vault_internal_route_attaches_to_vault_server():
    """vault.internal → host.docker.internal:8200, vault-server binds 8200."""
    intent = cp.parse_all()
    runtime, _ = di.inspect_all()
    merged, runtime_orphans, _ = di.merge_with_compose(intent, runtime)
    routes, _ = cr.read_routes()
    merged, _ = cr.attach_to_merged(merged, routes, runtime_orphans)
    vs = [r for r in merged if r["service_id"] == "vault-server"]
    assert vs, "vault-server missing from merged"
    cr_routes = vs[0]["addresses"]["caddy_routes"]
    assert any(c["external_host"] == "vault.internal" for c in cr_routes), (
        f"vault.internal not attached to vault-server; got {cr_routes}"
    )


def test_seal_vault_has_no_caddy_route():
    """Doctrine: seal-vault must NOT be externally exposed."""
    intent = cp.parse_all()
    runtime, _ = di.inspect_all()
    merged, runtime_orphans, _ = di.merge_with_compose(intent, runtime)
    routes, _ = cr.read_routes()
    merged, orphans = cr.attach_to_merged(merged, routes, runtime_orphans)
    sv = [r for r in merged if r["service_id"] == "seal-vault"]
    assert sv
    assert sv[0]["addresses"]["caddy_routes"] == [], (
        f"seal-vault unexpectedly has caddy routes: {sv[0]['addresses']['caddy_routes']}"
    )
    # And nobody else should claim seal-vault's port 8201 either
    for o in orphans:
        assert o["upstream_port"] != 8201, (
            f"unexpected caddy route to seal-vault port 8201: {o}"
        )


def test_homeassistant_header_transforms_preserved():
    """homeassistant.internal strips X-Forwarded-* headers — verify captured."""
    routes, src = cr.read_routes()
    ha = [r for r in routes if r.external_host == "homeassistant.internal"]
    assert ha, "homeassistant.internal route missing"
    # Multiple `header_up -X-...` directives. Both sources should capture some.
    assert ha[0].header_transforms, (
        f"header transforms lost from {src}: {ha[0]}"
    )


def test_runtime_orphans_get_caddy_routes_attached():
    """grafana-obs / obot / uptime-kuma are runtime-orphans (running but not
    in compose) — they MUST still receive their Caddy routes via the
    runtime-orphan match path, otherwise the registry under-reports
    external exposure."""
    intent = cp.parse_all()
    runtime, _ = di.inspect_all()
    merged, runtime_orphans, _ = di.merge_with_compose(intent, runtime)
    routes, _ = cr.read_routes()
    _, route_orphans = cr.attach_to_merged(merged, routes, runtime_orphans)
    # at least one of these well-known runtime-orphans should now carry a route
    attached_orphans = [
        o for o in runtime_orphans if o["addresses"]["caddy_routes"]
    ]
    names = {o["container_name"] for o in attached_orphans}
    expected_any = {"grafana-obs", "obot", "uptime-kuma"}
    assert names & expected_any, (
        f"none of {expected_any} got Caddy routes attached; "
        f"all attached orphans: {names}; route-orphans: "
        f"{[(o['external_host'], o['upstream_port']) for o in route_orphans]}"
    )


def test_route_orphans_are_non_containerized_only():
    """Anything left in route_orphans must be a host upstream that does not
    map to ANY running container (e.g. ollama running natively on macOS)."""
    intent = cp.parse_all()
    runtime, _ = di.inspect_all()
    merged, runtime_orphans, _ = di.merge_with_compose(intent, runtime)
    routes, _ = cr.read_routes()
    _, route_orphans = cr.attach_to_merged(merged, routes, runtime_orphans)
    all_host_ports: set[int] = set()
    for r in merged + runtime_orphans:
        for hm in r.get("addresses", {}).get("host_mapped", []) or []:
            if hm.get("host_port") is not None:
                all_host_ports.add(hm["host_port"])
    for o in route_orphans:
        if o["upstream_host"] == "host.docker.internal":
            assert o["upstream_port"] not in all_host_ports, (
                f"orphan {o['external_host']} → :{o['upstream_port']} but a "
                f"container IS bound to that port — attach logic missed it"
            )


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
