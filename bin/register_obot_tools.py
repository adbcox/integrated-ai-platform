#!/usr/bin/env python3
"""Register MCP tools with Obot.

Uses Obot's actual API format:
  POST /api/mcp-servers with {manifest: {runtime, name, npxConfig|uvxConfig|remoteConfig, env}}

Valid runtimes: npx, uvx, containerized, remote, composite

Usage:
    python3 bin/register_obot_tools.py              # register all READY tools
    python3 bin/register_obot_tools.py --check      # check what's registered
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
OBOT_URL = os.environ.get("OBOT_URL", "http://localhost:8090")

# Load docker/.env into os.environ
_dotenv = REPO_ROOT / "docker" / ".env"
if _dotenv.exists():
    for line in _dotenv.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            k = k.strip()
            if k and k not in os.environ:
                os.environ[k] = v.strip()

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
POSTGRES_DSN = os.environ.get("POSTGRES_DSN", "postgresql://plane:plane@docker-plane-db-1:5432/plane")
HA_TOKEN = os.environ.get("HA_TOKEN", "")
HA_BASE_URL = os.environ.get("HA_BASE_URL", "http://192.168.10.141:8123")
STRAVA_CLIENT_ID = os.environ.get("STRAVA_CLIENT_ID", "")
STRAVA_CLIENT_SECRET = os.environ.get("STRAVA_CLIENT_SECRET", "")
STRAVA_ACCESS_TOKEN = os.environ.get("STRAVA_ACCESS_TOKEN", "")
STRAVA_REFRESH_TOKEN = os.environ.get("STRAVA_REFRESH_TOKEN", "")

# ── Tool definitions ──────────────────────────────────────────────────────────
# Each entry maps to one POST /api/mcp-servers call.
# runtime: npx | uvx | remote | containerized
# npxConfig: {package, args}
# uvxConfig: {package, command, args}
# remoteConfig: {url}
# env: [{name, key, value, description, sensitive}]

TOOLS = [
    {
        "id": "filesystem",
        "manifest": {
            "name": "Filesystem",
            "shortDescription": "Read/write access to the IAP repository workspace",
            "runtime": "remote",
            "remoteConfig": {
                "url": "http://host.docker.internal:8091/mcp",
            },
        },
    },
    {
        "id": "postgresql",
        "manifest": {
            "name": "PostgreSQL (Plane)",
            "shortDescription": "Query Plane CE's Postgres database",
            "runtime": "npx",
            "npxConfig": {
                "package": "@modelcontextprotocol/server-postgres",
                "args": [POSTGRES_DSN],
            },
        },
    },
    {
        "id": "github",
        "manifest": {
            "name": "GitHub",
            "shortDescription": "Read/write GitHub repos, issues, PRs, and actions",
            "runtime": "npx",
            "npxConfig": {
                "package": "@modelcontextprotocol/server-github",
                "args": [],
            },
            "env": [
                {
                    "name": "GitHub Token",
                    "key": "GITHUB_PERSONAL_ACCESS_TOKEN",
                    "value": GITHUB_TOKEN,
                    "description": "GitHub PAT with repo scope",
                    "sensitive": True,
                }
            ],
        },
        "skip_if": not GITHUB_TOKEN,
        "skip_reason": "GITHUB_TOKEN not set in docker/.env",
    },
    {
        "id": "docker",
        "manifest": {
            "name": "Docker",
            "shortDescription": "Inspect and manage Docker containers, images, and volumes",
            "runtime": "remote",
            "remoteConfig": {
                "url": "http://host.docker.internal:8092/mcp",
            },
        },
    },
    {
        "id": "weather",
        "manifest": {
            "name": "Weather",
            "shortDescription": "Global weather: forecast, historical, air quality (open-meteo, no auth)",
            "runtime": "npx",
            "npxConfig": {
                "package": "open-meteo-mcp-server",
                "args": [],
            },
        },
    },
    {
        "id": "semgrep",
        "manifest": {
            "name": "Semgrep",
            "shortDescription": "Static analysis: scan directories, list rules, create/filter results",
            "runtime": "npx",
            "npxConfig": {
                "package": "mcp-server-semgrep",
                "args": [],
            },
        },
    },
    {
        "id": "health-fitness",
        "manifest": {
            "name": "Health & Fitness",
            "shortDescription": "BMI, TDEE, macros, workouts, heart rate zones, nutrition, sleep",
            "runtime": "npx",
            "npxConfig": {
                "package": "health-fitness-mcp",
                "args": [],
            },
        },
    },
    {
        "id": "docs",
        "manifest": {
            "name": "Docs",
            "shortDescription": "Scrape and search documentation for any library or framework",
            "runtime": "remote",
            "remoteConfig": {
                "url": "http://host.docker.internal:8093/mcp",
            },
        },
    },
    {
        "id": "home-assistant",
        "manifest": {
            "name": "Home Assistant",
            "shortDescription": "Smart home device control and state queries for 192.168.10.141",
            "runtime": "npx",
            "npxConfig": {
                "package": "home-mcp",
                "args": [],
            },
            "env": [
                {
                    "name": "HA Base URL",
                    "key": "HA_BASE_URL",
                    "value": HA_BASE_URL,
                    "description": "Home Assistant base URL",
                    "sensitive": False,
                },
                {
                    "name": "HA Token",
                    "key": "HA_TOKEN",
                    "value": HA_TOKEN,
                    "description": "Long-lived Home Assistant access token",
                    "sensitive": True,
                },
            ],
        },
        "skip_if": not HA_TOKEN,
        "skip_reason": "HA_TOKEN not set in docker/.env",
    },
    {
        "id": "strava",
        "manifest": {
            "name": "Strava",
            "shortDescription": "Triathlon training: activities, segments, routes, athlete stats (OAuth)",
            "runtime": "npx",
            "npxConfig": {
                "package": "strava-mcp-server",
                "args": [],
            },
            "env": [
                {
                    "name": "Strava Client ID",
                    "key": "STRAVA_CLIENT_ID",
                    "value": STRAVA_CLIENT_ID,
                    "description": "Numeric Strava API app client ID",
                    "sensitive": False,
                },
                {
                    "name": "Strava Client Secret",
                    "key": "STRAVA_CLIENT_SECRET",
                    "value": STRAVA_CLIENT_SECRET,
                    "description": "Strava API app client secret",
                    "sensitive": True,
                },
                {
                    "name": "Strava Access Token",
                    "key": "STRAVA_ACCESS_TOKEN",
                    "value": STRAVA_ACCESS_TOKEN,
                    "description": "OAuth access token (from OAuth flow)",
                    "sensitive": True,
                },
                {
                    "name": "Strava Refresh Token",
                    "key": "STRAVA_REFRESH_TOKEN",
                    "value": STRAVA_REFRESH_TOKEN,
                    "description": "OAuth refresh token (from OAuth flow)",
                    "sensitive": True,
                },
            ],
        },
        "skip_if": not (STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET and STRAVA_ACCESS_TOKEN),
        "skip_reason": "STRAVA_CLIENT_ID / STRAVA_ACCESS_TOKEN not set — complete OAuth flow first",
    },
]


def _request(method: str, path: str, body: dict | None = None) -> dict:
    url = f"{OBOT_URL}{path}"
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            content = r.read().decode()
            return json.loads(content) if content.strip() else {}
    except urllib.error.HTTPError as e:
        body_text = e.read().decode()[:300]
        return {"_error": e.code, "_body": body_text}


def wait_for_obot(retries: int = 30, delay: float = 2.0) -> bool:
    print(f"Waiting for Obot at {OBOT_URL}...")
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(f"{OBOT_URL}/api/healthz", method="GET")
            with urllib.request.urlopen(req, timeout=5) as r:
                if r.status == 200:
                    print(f"  Obot healthy (attempt {attempt})")
                    return True
        except Exception:
            pass
        print(f"  attempt {attempt}/{retries} — not ready yet")
        time.sleep(delay)
    return False


def list_registered() -> list[dict]:
    result = _request("GET", "/api/mcp-servers")
    return result.get("items", [])


def register_tool(tool: dict, existing_names: set[str]) -> bool:
    name = tool["manifest"]["name"]
    if name in existing_names:
        print(f"  already registered (skipping)")
        return True

    payload = {"manifest": tool["manifest"]}
    result = _request("POST", "/api/mcp-servers", payload)

    if "_error" in result:
        print(f"  FAILED — HTTP {result['_error']}: {result['_body']}")
        return False

    registered_id = result.get("id", "?")
    print(f"  registered (id={registered_id})")
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Only list what's registered")
    args = parser.parse_args()

    print("=" * 60)
    print("OBOT MCP SERVER REGISTRATION")
    print("=" * 60)
    print()

    if not wait_for_obot():
        print("Obot not reachable — aborting")
        sys.exit(1)
    print()

    if args.check:
        items = list_registered()
        if not items:
            print("No MCP servers registered yet.")
        else:
            print(f"{len(items)} registered server(s):")
            for item in items:
                name = item.get("manifest", {}).get("name", item.get("id", "?"))
                runtime = item.get("manifest", {}).get("runtime", "?")
                configured = item.get("configured", False)
                status = "configured" if configured else "not configured"
                print(f"  [{status}] {name} ({runtime})  id={item.get('id')}")
        return

    print(f"Registering {len(TOOLS)} server(s)...\n")
    existing_names = {
        item.get("manifest", {}).get("name", "")
        for item in list_registered()
    }
    ok = 0
    skipped = 0
    failed = 0

    for tool in TOOLS:
        print(f"→ {tool['id']} ({tool['manifest'].get('runtime')})")
        if tool.get("skip_if"):
            print(f"  SKIPPED — {tool.get('skip_reason', '')}")
            skipped += 1
            continue
        success = register_tool(tool, existing_names)
        if success:
            ok += 1
        else:
            failed += 1
        print()

    print("=" * 60)
    print(f"Done: {ok} registered, {skipped} skipped, {failed} failed")
    print()

    if failed:
        print("Re-run with --check to see what's registered.")
        sys.exit(1)

    print("Run with --check to verify all servers are configured.")


if __name__ == "__main__":
    main()
