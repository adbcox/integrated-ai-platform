#!/usr/bin/env python3
"""Register P0 MCP tools with Obot gateway and configure RBAC.

Run after `docker-compose -f docker/obot-stack.yml up -d`.

Usage:
    python3 bin/register_obot_tools.py              # register all P0 tools
    python3 bin/register_obot_tools.py --check      # verify tool health only
    python3 bin/register_obot_tools.py --register-claude  # also update ~/.claude.json

What this does:
    1. Waits for Obot to be healthy (retries 30x)
    2. Authenticates as admin
    3. Registers each P0 MCP tool (filesystem, postgres, plane, docker)
    4. Skips tools with missing credentials (GitHub without GITHUB_TOKEN)
    5. Configures RBAC roles (Admin, Dev, Agent)
    6. Optionally registers Obot as MCP server in ~/.claude.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
import urllib.request
import urllib.error

REPO_ROOT = Path(__file__).parent.parent
OBOT_URL = os.environ.get("OBOT_URL", "http://localhost:8090")
OBOT_ADMIN_USER = os.environ.get("OBOT_ADMIN_USERNAME", "admin")
OBOT_ADMIN_PASS = os.environ.get("OBOT_ADMIN_PASSWORD", "changeme_before_prod")

# Load docker/.env
_dotenv = REPO_ROOT / "docker" / ".env"
if _dotenv.exists():
    for line in _dotenv.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            if k.strip() and k.strip() not in os.environ:
                os.environ[k.strip()] = v.strip()


def _request(method: str, path: str, body: dict | None = None, token: str | None = None) -> dict:
    url = f"{OBOT_URL}{path}"
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            content = r.read().decode()
            return json.loads(content) if content.strip() else {}
    except urllib.error.HTTPError as e:
        body_text = e.read().decode()[:200]
        print(f"  HTTP {e.code} on {method} {path}: {body_text}")
        return {"error": e.code, "body": body_text}
    except Exception as e:
        return {"error": str(e)}


def wait_for_obot(max_retries: int = 30) -> bool:
    print(f"Waiting for Obot at {OBOT_URL}...")
    for i in range(max_retries):
        try:
            with urllib.request.urlopen(f"{OBOT_URL}/api/healthz", timeout=3):
                print(f"  Obot is healthy (attempt {i+1})")
                return True
        except Exception:
            pass
        time.sleep(3)
        sys.stdout.write(f"\r  Attempt {i+2}/{max_retries}...")
        sys.stdout.flush()
    print("\n  Obot did not become healthy")
    return False


def get_token() -> str | None:
    result = _request("POST", "/api/v1/auth/token", {
        "username": OBOT_ADMIN_USER,
        "password": OBOT_ADMIN_PASS,
    })
    return result.get("token") or result.get("access_token")


def register_tool(token: str, tool_def: dict) -> bool:
    tool_id = tool_def["id"]
    print(f"\n  Registering: {tool_id}")

    # Check for missing credentials
    status = tool_def.get("status", "READY")
    if status.startswith("BLOCKED_BY"):
        reason = status.replace("BLOCKED_BY_", "")
        print(f"  SKIPPED — blocked by: {reason}")
        return False

    payload = {
        "id": tool_id,
        "name": tool_def.get("name", tool_id),
        "description": tool_def.get("description", ""),
        "transport": tool_def.get("transport", "stdio"),
        "command": tool_def.get("command", ""),
        "args": tool_def.get("args", []),
        "env": {k: os.path.expandvars(str(v)) for k, v in tool_def.get("env", {}).items()},
    }

    result = _request("POST", f"/api/v1/tools", payload, token=token)
    if "error" in result:
        # Tool may already exist — try PUT
        result = _request("PUT", f"/api/v1/tools/{tool_id}", payload, token=token)

    if "error" not in result or result.get("error") == 409:
        print(f"  OK: {tool_id}")
        return True
    print(f"  FAILED: {result}")
    return False


def configure_rbac(token: str, roles: dict) -> None:
    print("\n  Configuring RBAC roles...")
    for role_name, role_def in roles.items():
        payload = {
            "name": role_name,
            "description": role_def.get("description", ""),
            "permissions": role_def.get("permissions", []),
        }
        result = _request("POST", "/api/v1/roles", payload, token=token)
        if "error" not in result or result.get("error") == 409:
            print(f"  Role '{role_name}': OK")
        else:
            print(f"  Role '{role_name}': {result}")


def register_with_claude_code() -> None:
    claude_json_path = Path.home() / ".claude.json"
    if not claude_json_path.exists():
        print("  ~/.claude.json not found — skipping Claude Code registration")
        return

    data = json.loads(claude_json_path.read_text())
    repo_key = str(REPO_ROOT)
    projects = data.setdefault("projects", {})
    project = projects.setdefault(repo_key, {})
    mcp_servers = project.setdefault("mcpServers", {})

    mcp_servers["obot-gateway"] = {
        "type": "http",
        "url": f"{OBOT_URL}/api/mcp",
        "headers": {
            "Authorization": f"Bearer {os.environ.get('OBOT_API_KEY', 'configure-obot-api-key')}"
        }
    }

    claude_json_path.write_text(json.dumps(data, indent=2))
    print(f"  Registered 'obot-gateway' in {claude_json_path}")


def check_tool_health(token: str) -> None:
    print("\n=== Tool Health Check ===")
    result = _request("GET", "/api/v1/tools", token=token)
    tools = result.get("items", result if isinstance(result, list) else [])
    if not tools:
        print("  No tools registered or Obot API format differs")
        return
    for t in tools:
        tid = t.get("id", "?")
        status = t.get("status", "unknown")
        print(f"  {tid}: {status}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Check tool health only")
    parser.add_argument("--register-claude", action="store_true", help="Register Obot in ~/.claude.json")
    args = parser.parse_args()

    # Load tool/RBAC definitions
    import yaml
    tools_path = REPO_ROOT / "config" / "obot" / "tools.yaml"
    rbac_path = REPO_ROOT / "config" / "obot" / "rbac.yaml"

    try:
        tools_cfg = yaml.safe_load(tools_path.read_text())
        rbac_cfg = yaml.safe_load(rbac_path.read_text())
    except ImportError:
        print("yaml not available — using json fallback")
        tools_cfg = {"tools": {}}
        rbac_cfg = {"roles": {}}

    if not wait_for_obot():
        print("\nObot is not reachable. Start it first:")
        print("  cd docker && docker-compose -f obot-stack.yml up -d")
        sys.exit(1)

    token = get_token()
    if not token:
        print("\nCould not authenticate with Obot. Check OBOT_ADMIN_PASSWORD.")
        print("  If first run, Obot may use a different auth flow — check http://localhost:8090")
        # Continue with check even without token
        if args.check:
            check_tool_health(None)
        sys.exit(1)

    if args.check:
        check_tool_health(token)
        return

    print("\n=== Registering P0 MCP Tools ===")
    tools = tools_cfg.get("tools", {})
    registered = 0
    skipped = 0
    for name, tool_def in tools.items():
        tool_def["id"] = tool_def.get("id", f"{name}-mcp")
        if register_tool(token, tool_def):
            registered += 1
        else:
            skipped += 1

    print(f"\n  Registered: {registered} | Skipped/blocked: {skipped}")

    configure_rbac(token, rbac_cfg.get("roles", {}))

    if args.register_claude:
        print("\n=== Registering Obot with Claude Code ===")
        register_with_claude_code()

    print("\n=== Summary ===")
    print(f"  Obot gateway: {OBOT_URL}")
    print(f"  Admin UI:     {OBOT_URL}/")
    print(f"  Audit log:    docker exec obot tail -f /data/audit.log")
    print(f"  MCP endpoint: {OBOT_URL}/api/mcp")
    print(f"\n  To use in Claude Code:")
    print(f"    python3 bin/register_obot_tools.py --register-claude")


if __name__ == "__main__":
    main()
