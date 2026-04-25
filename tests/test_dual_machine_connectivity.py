"""Connectivity tests for Mac Mini ↔ Mac Studio dual-node setup.

Run with: python3 -m pytest tests/test_dual_machine_connectivity.py -v
Skips gracefully when Mac Studio is not yet on the network.
"""
from __future__ import annotations

import os
import socket
import urllib.request
import pytest

MAC_MINI_IP   = "127.0.0.1"         # localhost when run on Mac Mini
MAC_STUDIO_IP = os.environ.get("MAC_STUDIO_IP", "192.168.10.202")

OLLAMA_PORT        = 11434
PLATFORM_PORT      = 8080
VICTORIA_PORT      = 8428
PLANE_PORT         = 8000


def _tcp_ok(host: str, port: int, timeout: float = 2.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _http_ok(url: str, timeout: float = 5.0) -> bool:
    import http.client, urllib.parse
    try:
        p = urllib.parse.urlparse(url)
        conn = http.client.HTTPConnection(p.hostname, p.port or 80, timeout=timeout)
        conn.request("GET", p.path or "/")
        r = conn.getresponse()
        r.read()  # drain to avoid connection issues
        conn.close()
        return r.status < 500
    except Exception:
        return False


def studio_reachable() -> bool:
    return _tcp_ok(MAC_STUDIO_IP, 22, timeout=1.0)


# ── Mac Mini local services ───────────────────────────────────────────────────

def test_platform_dashboard_up():
    assert _tcp_ok(MAC_MINI_IP, PLATFORM_PORT), \
        f"Dashboard not listening on :{PLATFORM_PORT} — is server.py running?"


def test_platform_api_status():
    assert _http_ok(f"http://{MAC_MINI_IP}:{PLATFORM_PORT}/api/status", timeout=12.0), \
        "/api/status returned an error"


def test_plane_api_up():
    assert _tcp_ok(MAC_MINI_IP, PLANE_PORT), \
        f"Plane CE not listening on :{PLANE_PORT}"


def test_victoria_metrics_up():
    assert _tcp_ok(MAC_MINI_IP, VICTORIA_PORT), \
        f"VictoriaMetrics not listening on :{VICTORIA_PORT}"


def test_ollama_mini_up():
    assert _tcp_ok(MAC_MINI_IP, OLLAMA_PORT), \
        f"Ollama not listening on Mac Mini :{OLLAMA_PORT}"


# ── Mac Studio remote services ────────────────────────────────────────────────

@pytest.mark.skipif(not studio_reachable(), reason="Mac Studio not on network yet")
def test_studio_ssh_reachable():
    assert _tcp_ok(MAC_STUDIO_IP, 22), \
        f"SSH not reachable at {MAC_STUDIO_IP}:22"


@pytest.mark.skipif(not studio_reachable(), reason="Mac Studio not on network yet")
def test_studio_ollama_up():
    assert _tcp_ok(MAC_STUDIO_IP, OLLAMA_PORT), \
        f"Ollama not listening on Mac Studio {MAC_STUDIO_IP}:{OLLAMA_PORT}"


@pytest.mark.skipif(not studio_reachable(), reason="Mac Studio not on network yet")
def test_studio_ollama_api():
    url = f"http://{MAC_STUDIO_IP}:{OLLAMA_PORT}/api/tags"
    assert _http_ok(url), f"Ollama /api/tags not responding at {url}"


@pytest.mark.skipif(not studio_reachable(), reason="Mac Studio not on network yet")
def test_studio_ollama_has_models():
    import json
    url = f"http://{MAC_STUDIO_IP}:{OLLAMA_PORT}/api/tags"
    try:
        with urllib.request.urlopen(url, timeout=4.0) as r:
            data = json.load(r)
        models = [m["name"] for m in data.get("models", [])]
        assert models, "Mac Studio Ollama has no models pulled yet"
    except Exception as e:
        pytest.fail(f"Could not read Mac Studio model list: {e}")


# ── Cross-machine round-trip ──────────────────────────────────────────────────

@pytest.mark.skipif(not studio_reachable(), reason="Mac Studio not on network yet")
def test_platform_can_reach_studio_ollama():
    """Simulate the platform routing an inference request to Mac Studio."""
    url = f"http://{MAC_STUDIO_IP}:{OLLAMA_PORT}/api/tags"
    assert _http_ok(url), \
        "Platform cannot reach Mac Studio Ollama — check firewall / OLLAMA_HOST setting"
