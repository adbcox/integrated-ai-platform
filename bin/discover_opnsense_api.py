#!/usr/bin/env python3
"""Auto-extract OPNsense API key + secret via web scraping.

OPNsense 26.x uses:
  - Login: POST / with CSRF hidden field + usernamefld/passwordfld
  - User search: GET /api/auth/user/search  (returns UUIDs)
  - API key generation: POST /api/auth/user/addApiKey/{uuid}  (needs X-CSRFToken header)
  - User management UI: /ui/auth/user
"""
from __future__ import annotations

import http.cookiejar
import json
import os
import re
import ssl
import sys
import urllib.parse
import urllib.request

OPNSENSE_URL = os.environ.get("OPNSENSE_URL", "https://192.168.10.1")

# Ordered list of credential pairs to try
CREDENTIAL_CANDIDATES = [
    ("root",  "opnsense"),
    ("root",  "+Huckbear17"),
    ("admin", "+Huckbear17"),
    ("admin", "opnsense"),
]

_CTX = ssl.create_default_context()
_CTX.check_hostname = False
_CTX.verify_mode    = ssl.CERT_NONE


def _make_opener():
    cj  = http.cookiejar.CookieJar()
    opr = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cj),
        urllib.request.HTTPSHandler(context=_CTX),
    )
    return opr, cj


def _get_csrf(opener, url: str) -> tuple[str, str]:
    """Fetch URL, return (csrf_field_name, csrf_value)."""
    resp = opener.open(url, timeout=12)
    body = resp.read().decode(errors="replace")
    m = re.search(
        r'<input[^>]+type=["\']hidden["\'][^>]+name=["\']([^"\']+)["\'][^>]+value=["\']([^"\']+)["\']',
        body, re.IGNORECASE,
    )
    if not m:
        m = re.search(r'name=["\']([^"\']{5,})["\'] value=["\']([A-Za-z0-9_\-]{10,})["\']', body)
    if not m:
        raise RuntimeError("CSRF token not found in page")
    return m.group(1), m.group(2)


def login() -> tuple[urllib.request.OpenerDirector | None, str | None, str | None, str | None]:
    """Try all credential candidates; return (opener, username, password, csrf_token) on success."""
    for username, password in CREDENTIAL_CANDIDATES:
        try:
            opener, _ = _make_opener()
            csrf_field, csrf_val = _get_csrf(opener, f"{OPNSENSE_URL}/")

            post_data = urllib.parse.urlencode({
                csrf_field:    csrf_val,
                "usernamefld": username,
                "passwordfld": password,
                "login":       "Login",
            }).encode()
            resp = opener.open(
                urllib.request.Request(f"{OPNSENSE_URL}/", data=post_data, method="POST"),
                timeout=12,
            )
            body = resp.read().decode(errors="replace")

            failed = ("Invalid username" in body
                      or ("usernamefld" in body and "passwordfld" in body))
            if not failed:
                print(f"  ✓ Logged in as {username}")
                return opener, username, password, csrf_val
            else:
                print(f"    {username}/{password[:6]}… → rejected")
        except Exception as e:
            print(f"    {username} error: {e}")

    return None, None, None, None


def get_api_keys(opener, csrf_val: str) -> tuple[str | None, str | None]:
    """Try OPNsense 26.x API endpoints to generate a new API key for root."""
    # Step 1: Find the root user UUID via the auth API
    try:
        resp = opener.open(f"{OPNSENSE_URL}/api/auth/user/search", timeout=12)
        data = json.loads(resp.read())
        rows = data.get("rows", [])
        print(f"  Users found: {[r.get('name') for r in rows]}")
    except Exception as e:
        print(f"  User search error: {e}")
        return None, None

    # Try addApiKey for each user
    for user in rows:
        uuid = user.get("uuid")
        name = user.get("name")
        if not uuid:
            continue
        try:
            req = urllib.request.Request(
                f"{OPNSENSE_URL}/api/auth/user/addApiKey/{uuid}",
                data=b"{}",
                headers={"Content-Type": "application/json", "X-CSRFToken": csrf_val},
                method="POST",
            )
            r = opener.open(req, timeout=12)
            result = json.loads(r.read())
            if result.get("result") not in ("failed", None) or result.get("key"):
                key    = result.get("key")    or result.get("api_key")
                secret = result.get("secret") or result.get("api_secret")
                if key and secret:
                    print(f"  ✓ Generated API key for user {name}")
                    return key, secret
            print(f"  addApiKey({name}): {result}")
        except Exception as e:
            print(f"  addApiKey({name}) error: {e}")

    return None, None


def main() -> int:
    print(f"Connecting to OPNsense at {OPNSENSE_URL}…")

    opener, username, _, csrf_val = login()
    if not opener:
        print("\n❌ All login attempts failed")
        _print_manual()
        return 1

    print("  Trying to generate API key…")
    api_key, api_secret = get_api_keys(opener, csrf_val or "")

    if api_key and api_secret:
        print(f"\nOPNSENSE_API_KEY={api_key}")
        print(f"OPNSENSE_API_SECRET={api_secret}")
        return 0

    print("\n❌ Could not auto-generate OPNsense API credentials")
    print("   (OPNsense 26.x may restrict API key generation for the root system user)")
    _print_manual()
    return 1


def _print_manual() -> None:
    print("\nManual steps (2 min):")
    print(f"  1. Open: {OPNSENSE_URL}/ui/auth/user")
    print(f"  2. Login: root / opnsense")
    print("  3. Click the pencil icon on the root user")
    print("  4. Scroll to 'API keys' → click [+] → download .key file")
    print("  5. Run:  python3 bin/update_all_credentials.py \\")
    print("             --opnsense-key KEY --opnsense-secret SECRET")


if __name__ == "__main__":
    sys.exit(main())
