#!/usr/bin/env python3
"""Fully automate Plane CE first-run setup — no browser required.

Performs in order:
  1. Wait for Plane API to be reachable
  2. Trigger the instance "magic-link" / setup-complete flag via Django shell
  3. Create the admin user account (POST /auth/sign-up/)
  4. Sign in to get a JWT (POST /auth/sign-in/)
  5. Create a permanent API token (POST /api/users/api-tokens/)
  6. Create workspace slug=iap (POST /api/v1/workspaces/)
  7. Create project "Roadmap" (POST /api/v1/workspaces/iap/projects/)
  8. Write PLANE_API_TOKEN + PLANE_PROJECT_ID into docker/.env
  9. Run configure_plane_agile.py (states, labels, cycles, modules)
  10. Run sync_roadmap_to_plane.py --init then full sync

Usage (from repo root):
    python3 bin/setup_plane_automated.py
    python3 bin/setup_plane_automated.py --dry-run   # skip writes / syncs
    python3 bin/setup_plane_automated.py --skip-sync # skip the 600-item sync

Environment (from docker/.env or shell):
    PLANE_URL           default http://localhost:8000
    PLANE_ADMIN_EMAIL   default admin@local.dev
    PLANE_ADMIN_PASSWORD
    PLANE_WORKSPACE     default iap
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_REPO_ROOT))

# ── Env defaults ─────────────────────────────────────────────────────────────

def _load_dotenv() -> dict[str, str]:
    """Parse docker/.env (if present) and return key→value dict."""
    env_file = _REPO_ROOT / "docker" / ".env"
    result: dict[str, str] = {}
    if not env_file.exists():
        return result
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        result[k.strip()] = v.strip()
    return result


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key) or _DOTENV.get(key, default)


_DOTENV: dict[str, str] = {}  # populated in main()


# ── HTTP helpers ──────────────────────────────────────────────────────────────

def _request(
    method: str,
    url: str,
    *,
    data: dict | None = None,
    headers: dict[str, str] | None = None,
    json_body: bool = True,
    timeout: int = 30,
) -> dict:
    """Make an HTTP request and return parsed JSON response."""
    body: bytes | None = None
    req_headers = headers or {}

    if data is not None:
        if json_body:
            body = json.dumps(data).encode()
            req_headers.setdefault("Content-Type", "application/json")
        else:
            body = urllib.parse.urlencode(data).encode()
            req_headers.setdefault("Content-Type", "application/x-www-form-urlencoded")

    req = urllib.request.Request(url, data=body, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode(errors="replace")[:500]
        raise RuntimeError(f"HTTP {exc.code} {method} {url}: {body_text}") from exc


def _get(url: str, token: str = "", jwt: str = "") -> dict:
    headers: dict[str, str] = {}
    if token:
        headers["X-Api-Key"] = token
    elif jwt:
        headers["Authorization"] = f"Bearer {jwt}"
    return _request("GET", url, headers=headers)


def _post(url: str, data: dict, token: str = "", jwt: str = "", json_body: bool = True) -> dict:
    headers: dict[str, str] = {}
    if token:
        headers["X-Api-Key"] = token
    elif jwt:
        headers["Authorization"] = f"Bearer {jwt}"
    return _request("POST", url, data=data, headers=headers, json_body=json_body)


# ── Step 1: Wait for API ──────────────────────────────────────────────────────

def wait_for_plane(base_url: str, timeout: int = 120) -> None:
    print(f"[1/9] Waiting for Plane API at {base_url} …", end="", flush=True)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(base_url + "/", timeout=5) as r:
                if r.status == 200:
                    print(" ready.")
                    return
        except Exception:
            pass
        print(".", end="", flush=True)
        time.sleep(3)
    raise RuntimeError(f"Plane API not reachable at {base_url} after {timeout}s")


# ── Step 2: Mark instance setup done ─────────────────────────────────────────

def mark_instance_setup_done(dry_run: bool = False) -> None:
    """
    Plane requires instance.is_setup_done == True before the first sign-up.
    The Instance model lives in the 'license' app (plane.license.models.instance).
    We set it via docker exec into the running plane-api container.
    """
    print("[2/9] Marking instance setup as done …")
    py_snippet = (
        "import os; os.environ['DJANGO_SETTINGS_MODULE']='plane.settings.production'; "
        "import django; django.setup(); "
        "from django.apps import apps; from django.utils import timezone; "
        "Instance = apps.get_model('license', 'Instance'); "
        "qs = Instance.objects.all(); "
        "inst = qs.first() if qs.exists() else Instance.objects.create("
        "  instance_name='IAP Instance', instance_id='00000000-0000-0000-0000-000000000001',"
        "  last_checked_at=timezone.now(), edition='PLANE_COMMUNITY',"
        "  is_setup_done=True, is_signup_screen_visited=True,"
        "  is_telemetry_enabled=False, is_support_required=False,"
        "  is_verified=False, is_test=False, is_current_version_deprecated=False); "
        "inst.is_setup_done = True; inst.is_signup_screen_visited = True; "
        "inst.save(update_fields=['is_setup_done', 'is_signup_screen_visited']); "
        "print('instance.is_setup_done =', inst.is_setup_done)"
    )

    # Try both common container names (varies by compose project name)
    container_names = ["docker-plane-api-1", "plane-api-1", "integrated-ai-platform-plane-api-1"]

    if dry_run:
        print(f"  [DRY] would docker exec into plane-api container to set is_setup_done=True")
        return

    for container in container_names:
        cmd = ["docker", "exec", container, "python3", "-c", py_snippet]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print(f"  {result.stdout.strip()}")
                return
            if "No such container" in result.stderr or "Error: No such container" in result.stderr:
                continue
            raise RuntimeError(result.stderr.strip()[:300])
        except subprocess.TimeoutExpired:
            continue

    raise RuntimeError(
        "Could not find plane-api container. Check name with: docker ps | grep plane-api"
    )


# ── Step 3: Create admin account (via Django ORM — bypasses CSRF) ────────────

def create_account(base_url: str, email: str, password: str, dry_run: bool = False) -> None:
    """
    Create the admin user directly via Docker exec into plane-api.
    Using the HTTP sign-up endpoint requires CSRF cookies and doesn't return a JSON
    body (it redirects). Django ORM creation is simpler and always works.
    """
    print(f"[3/9] Creating admin account: {email} …")
    py_snippet = (
        f"import os; os.environ['DJANGO_SETTINGS_MODULE']='plane.settings.production'; "
        f"import django; django.setup(); "
        f"from django.contrib.auth import get_user_model; "
        f"User = get_user_model(); "
        f"qs = User.objects.filter(email='{email}'); "
        f"user = qs.first() if qs.exists() else User.objects.create_user("
        f"  username='{email}', email='{email}', password='{password}',"
        f"  display_name='Admin', is_active=True); "
        f"print('user:', user.pk, user.email)"
    )
    container_names = ["docker-plane-api-1", "plane-api-1", "integrated-ai-platform-plane-api-1"]
    if dry_run:
        print("  [DRY] skipping")
        return
    for container in container_names:
        cmd = ["docker", "exec", container, "python3", "-c", py_snippet]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print(f"  {result.stdout.strip()}")
                return
            if "No such container" in result.stderr:
                continue
            raise RuntimeError(result.stderr.strip()[:300])
        except subprocess.TimeoutExpired:
            continue
    raise RuntimeError("Could not find plane-api container")


# ── Step 4: Sign in → session cookie ─────────────────────────────────────────

def sign_in(base_url: str, email: str, password: str) -> tuple[str, str]:
    """
    Sign in using Plane's CSRF-protected form endpoint.
    Returns (session_id, csrf_cookie) for use in subsequent session-auth calls.
    Plane uses SessionAuthentication — not JWT — for its /api/ endpoints.
    """
    print(f"[4/9] Signing in as {email} …")
    # 1. Get a fresh CSRF token
    csrf_resp = _request("GET", f"{base_url}/auth/get-csrf-token/")
    csrf_token: str = csrf_resp.get("csrf_token", "")
    if not csrf_token:
        raise RuntimeError("Could not fetch CSRF token from /auth/get-csrf-token/")

    # 2. POST sign-in with CSRF header + cookie (form-encoded)
    import http.cookiejar
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    body = urllib.parse.urlencode({"email": email, "password": password}).encode()
    req = urllib.request.Request(
        f"{base_url}/auth/sign-in/",
        data=body,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "X-CSRFToken": csrf_token,
            "Cookie": f"csrftoken={csrf_token}",
        },
        method="POST",
    )
    try:
        with opener.open(req, timeout=15) as resp:
            # Success = redirect to localhost:3001 (302 followed to 405 by nginx)
            # We only care about the session-id cookie
            pass
    except urllib.error.HTTPError as exc:
        if exc.code not in (302, 405):
            raise RuntimeError(f"Sign-in failed: HTTP {exc.code}") from exc

    session_id = ""
    csrf_cookie = csrf_token
    for cookie in cj:
        if cookie.name == "session-id":
            session_id = cookie.value
        elif cookie.name == "csrftoken":
            csrf_cookie = cookie.value

    if not session_id:
        raise RuntimeError("Sign-in did not return a session-id cookie")

    print(f"  Session established (session-id length {len(session_id)}).")
    return session_id, csrf_cookie


# ── Step 5: Create permanent API token ───────────────────────────────────────

def create_api_token(base_url: str, session_id: str, csrf_cookie: str, label: str = "dashboard-sync") -> str:
    """Create a permanent API token using the session cookie for auth."""
    print(f"[5/9] Creating permanent API token '{label}' …")
    resp = _request(
        "POST",
        f"{base_url}/api/users/api-tokens/",
        data={"label": label, "expired_at": None},
        headers={
            "Content-Type": "application/json",
            "X-CSRFToken": csrf_cookie,
            "Cookie": f"csrftoken={csrf_cookie}; session-id={session_id}",
        },
        json_body=True,
    )
    token = resp.get("token", "")
    if not token:
        raise RuntimeError(f"Could not find token in response: {list(resp.keys())}")
    print(f"  Token created: {token[:8]}…")
    return token


# ── Step 6: Create workspace ─────────────────────────────────────────────────

def create_workspace(base_url: str, session_id: str, csrf_cookie: str,
                     slug: str, name: str = "IAP") -> None:
    print(f"[6/9] Creating workspace slug='{slug}' …")
    cookies = f"csrftoken={csrf_cookie}; session-id={session_id}"
    try:
        resp = _request(
            "POST",
            f"{base_url}/api/workspaces/",
            data={"name": name, "slug": slug, "organization_size": "10"},
            headers={"Content-Type": "application/json", "X-CSRFToken": csrf_cookie, "Cookie": cookies},
        )
        print(f"  Workspace: {resp.get('name', '?')} ({resp.get('slug', '?')})")
    except RuntimeError as exc:
        msg = str(exc)
        if "already exists" in msg.lower() or "400" in msg or "409" in msg:
            print(f"  Workspace '{slug}' already exists. Continuing.")
        else:
            raise


# ── Step 7: Create project ───────────────────────────────────────────────────

def create_project(base_url: str, session_id: str, csrf_cookie: str,
                   workspace: str, name: str = "Roadmap") -> str:
    print(f"[7/9] Creating project '{name}' in workspace '{workspace}' …")
    cookies = f"csrftoken={csrf_cookie}; session-id={session_id}"
    try:
        resp = _request(
            "POST",
            f"{base_url}/api/workspaces/{workspace}/projects/",
            data={
                "name": name,
                "identifier": "RM",
                "description": "Platform roadmap — 600+ items tracked from docs/roadmap/ITEMS/*.md",
            },
            headers={"Content-Type": "application/json", "X-CSRFToken": csrf_cookie, "Cookie": cookies},
        )
        project_id = resp.get("id", "")
        print(f"  Project created. UUID: {project_id}")
        # Enable cycles and modules
        _request("PATCH", f"{base_url}/api/workspaces/{workspace}/projects/{project_id}/",
                 data={"cycle_view": True, "module_view": True},
                 headers={"Content-Type": "application/json", "X-CSRFToken": csrf_cookie, "Cookie": cookies})
        return project_id
    except RuntimeError as exc:
        msg = str(exc)
        if "already exists" in msg.lower() or "400" in msg or "409" in msg:
            print(f"  Project already exists. Fetching UUID …")
            projects = _request("GET", f"{base_url}/api/workspaces/{workspace}/projects/",
                                headers={"Cookie": cookies})
            items = projects if isinstance(projects, list) else projects.get("results", [])
            for p in items:
                if p.get("name") == name or p.get("identifier") == "RM":
                    pid = p.get("id", "")
                    print(f"  Found project UUID: {pid}")
                    return pid
            raise RuntimeError("Could not find or create Roadmap project")
        raise


# ── Step 8: Write docker/.env ────────────────────────────────────────────────

def update_dotenv(token: str, project_id: str, workspace: str, dry_run: bool = False) -> None:
    print("[8/9] Writing credentials to docker/.env …")
    env_file = _REPO_ROOT / "docker" / ".env"

    if not env_file.exists():
        print(f"  WARNING: {env_file} not found — printing values to stdout instead")
        print(f"  PLANE_API_TOKEN={token}")
        print(f"  PLANE_PROJECT_ID={project_id}")
        print(f"  PLANE_WORKSPACE={workspace}")
        return

    if dry_run:
        print(f"  [DRY] would write PLANE_API_TOKEN and PLANE_PROJECT_ID to {env_file}")
        return

    content = env_file.read_text()

    def _replace_or_append(text: str, key: str, value: str) -> str:
        pattern = rf"^{re.escape(key)}=.*$"
        replacement = f"{key}={value}"
        if re.search(pattern, text, re.MULTILINE):
            return re.sub(pattern, replacement, text, flags=re.MULTILINE)
        return text.rstrip("\n") + f"\n{replacement}\n"

    content = _replace_or_append(content, "PLANE_API_TOKEN", token)
    content = _replace_or_append(content, "PLANE_PROJECT_ID", project_id)
    content = _replace_or_append(content, "PLANE_WORKSPACE", workspace)

    env_file.write_text(content)
    print(f"  Written to {env_file}")


# ── Step 9a: Run configure_plane_agile.py ─────────────────────────────────────

def run_agile_config(base_url: str, token: str, workspace: str, project_id: str, dry_run: bool = False) -> None:
    print("[9a/9] Running configure_plane_agile.py …")
    script = _REPO_ROOT / "bin" / "configure_plane_agile.py"
    if not script.exists():
        print("  SKIP: configure_plane_agile.py not found")
        return

    env = {
        **os.environ,
        "PLANE_URL": base_url,
        "PLANE_API_TOKEN": token,
        "PLANE_WORKSPACE": workspace,
        "PLANE_PROJECT_ID": project_id,
    }
    cmd = [sys.executable, str(script)]
    if dry_run:
        print(f"  [DRY] would run: {' '.join(cmd)}")
        return

    result = subprocess.run(cmd, env=env, capture_output=False, timeout=120)
    if result.returncode != 0:
        print(f"  WARNING: configure_plane_agile.py exited {result.returncode}")


# ── Step 9b: Sync roadmap to Plane ───────────────────────────────────────────

def run_roadmap_sync(base_url: str, token: str, workspace: str, project_id: str,
                     skip_sync: bool = False, dry_run: bool = False) -> None:
    print("[9b/9] Running sync_roadmap_to_plane.py …")
    script = _REPO_ROOT / "bin" / "sync_roadmap_to_plane.py"
    if not script.exists():
        print("  SKIP: sync_roadmap_to_plane.py not found")
        return

    if skip_sync:
        print("  SKIP: --skip-sync flag set")
        return

    env = {
        **os.environ,
        "PLANE_URL": base_url,
        "PLANE_API_TOKEN": token,
        "PLANE_WORKSPACE": workspace,
        "PLANE_PROJECT_ID": project_id,
    }

    # --init first: create states and labels
    cmd_init = [sys.executable, str(script), "--init"]
    if dry_run:
        print(f"  [DRY] would run: {' '.join(cmd_init)}")
        print(f"  [DRY] would run: {sys.executable} {script}")
        return

    print("  Running --init (states + labels) …")
    subprocess.run(cmd_init, env=env, timeout=60)

    # Full sync
    print("  Running full sync (this takes ~3 minutes for 600 items) …")
    subprocess.run([sys.executable, str(script)], env=env, timeout=600)


# ── Summary ───────────────────────────────────────────────────────────────────

def print_summary(base_url: str, token: str, workspace: str, project_id: str) -> None:
    print("\n" + "=" * 60)
    print("  Plane setup complete!")
    print("=" * 60)
    print(f"  Web UI:        http://localhost:3001")
    print(f"  API:           {base_url}")
    print(f"  Workspace:     {workspace}")
    print(f"  Project UUID:  {project_id}")
    print(f"  API Token:     {token[:8]}…")
    print()
    print("  To register with Claude Code:")
    print(f"    claude mcp add plane-roadmap \\")
    print(f"      --command python3 \\")
    print(f"      --args {_REPO_ROOT}/mcp/plane_mcp_server.py \\")
    print(f"      --env PLANE_URL={base_url} \\")
    print(f"      --env PLANE_API_TOKEN={token} \\")
    print(f"      --env PLANE_WORKSPACE={workspace} \\")
    print(f"      --env PLANE_PROJECT_ID={project_id}")
    print()
    print("  Or run:  bash bin/register_plane_mcp.sh")
    print("=" * 60)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    global _DOTENV
    _DOTENV = _load_dotenv()

    parser = argparse.ArgumentParser(
        description="Fully automate Plane CE first-run setup (no browser required)"
    )
    parser.add_argument("--dry-run",    action="store_true", help="Translate but don't write or run syncs")
    parser.add_argument("--skip-sync",  action="store_true", help="Skip the 600-item roadmap sync")
    parser.add_argument("--skip-instance-setup", action="store_true",
                        help="Skip Step 2 (instance setup already done)")
    parser.add_argument("--url",       default=_env("PLANE_URL", "http://localhost:8000"))
    parser.add_argument("--email",     default=_env("PLANE_ADMIN_EMAIL", "admin@local.dev"))
    parser.add_argument("--password",  default=_env("PLANE_ADMIN_PASSWORD", "Admin1234!"))
    parser.add_argument("--workspace", default=_env("PLANE_WORKSPACE", "iap"))
    args = parser.parse_args()

    base_url  = args.url.rstrip("/")
    email     = args.email
    password  = args.password
    workspace = args.workspace

    if not password:
        print("ERROR: PLANE_ADMIN_PASSWORD not set in docker/.env or environment")
        sys.exit(1)

    # Run steps
    wait_for_plane(base_url)

    if not args.skip_instance_setup:
        mark_instance_setup_done(dry_run=args.dry_run)

    create_account(base_url, email, password, dry_run=args.dry_run)

    if args.dry_run:
        session_id = "dry-run-session"
        csrf_cookie = "dry-run-csrf"
        token = "dry-run-token"
        project_id = "dry-run-uuid"
    else:
        session_id, csrf_cookie = sign_in(base_url, email, password)
        token = create_api_token(base_url, session_id, csrf_cookie)
        create_workspace(base_url, session_id, csrf_cookie, workspace)
        project_id = create_project(base_url, session_id, csrf_cookie, workspace)

    update_dotenv(token, project_id, workspace, dry_run=args.dry_run)
    run_agile_config(base_url, token, workspace, project_id, dry_run=args.dry_run)
    run_roadmap_sync(base_url, token, workspace, project_id,
                     skip_sync=args.skip_sync, dry_run=args.dry_run)

    if not args.dry_run:
        print_summary(base_url, token, workspace, project_id)
    else:
        print("\n[DRY RUN complete — no changes made]")


if __name__ == "__main__":
    main()
