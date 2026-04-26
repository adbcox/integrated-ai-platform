#!/usr/bin/env python3
"""
ingest-docs.py — Upload platform docs into AnythingLLM workspaces

Usage:
    python3 bin/ingest-docs.py --workspace engineering
    python3 bin/ingest-docs.py --workspace roadmap
    python3 bin/ingest-docs.py --list
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error

BASE_URL = os.environ.get("ANYTHINGLLM_URL", "http://localhost:3004")
API_KEY = os.environ.get("ANYTHINGLLM_API_KEY", "sk-iap-d9fb40b796944234882c7b54908f603f")
DOCS_ROOT = os.environ.get("DOCS_ROOT", os.path.join(os.path.dirname(__file__), "..", "docs"))

WORKSPACE_DOCS = {
    "engineering": [
        "PLATFORM_OVERVIEW.md",
        "ARCHITECTURE.md",
        "DEPLOYMENT_GUIDE.md",
        "TROUBLESHOOTING.md",
        "QUICK_REFERENCE.md",
        "DEPLOYMENT_ARCHITECTURE.md",
        "NETWORK_ARCHITECTURE.md",
        "SYSTEMS_GUIDE.md",
        "architecture/MASTER_SYSTEM_ARCHITECTURE.md",
        "architecture/DECISION_REGISTER.md",
        "architecture/AUTHORITY_SURFACES.md",
        "adr/README.md",
        "adr/ADR-A-001.md",
        "adr/ADR-A-006.md",
        "adr/ADR-A-007.md",
        "adr/ADR-A-008.md",
    ],
    "roadmap": [
        "STRATEGIC_PLAN.md",
        "PHASE_5_CHECKLIST.md",
        "PHASE_6_CHECKLIST.md",
        "ROADMAP_GOVERNANCE_IMPLEMENTATION.md",
        "AUTONOMOUS_ROADMAP_GUIDE.md",
        "governance/CURRENT_OPERATING_CONTEXT.md",
        "governance/DOCUMENT_STATE_INDEX.md",
    ],
}

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}


def api(method, path, body=None):
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.read().decode()[:200]}"}
    except Exception as e:
        return {"error": str(e)}


def upload_raw_text(title, content, workspace_slug=None):
    body = {
        "textContent": content,
        "metadata": {"title": title, "docSource": "platform-docs"},
        "addToWorkspaces": workspace_slug if workspace_slug else "",
    }
    result = api("POST", "/api/v1/document/raw-text", body)
    return result


def list_documents():
    result = api("GET", "/api/v1/documents")
    docs = result.get("localFiles", {}).get("items", [])
    print(f"Documents in AnythingLLM ({len(docs)} total):")
    for d in docs:
        print(f"  {d.get('name', '?')} — {d.get('id', '?')}")


def ingest_workspace(workspace_slug):
    files = WORKSPACE_DOCS.get(workspace_slug)
    if not files:
        print(f"ERROR: unknown workspace '{workspace_slug}'. Valid: {list(WORKSPACE_DOCS.keys())}")
        sys.exit(1)

    workspaces = api("GET", "/api/v1/workspaces").get("workspaces", [])
    matched = [w for w in workspaces if w["slug"].startswith(workspace_slug)]
    if not matched:
        print(f"ERROR: workspace '{workspace_slug}' not found in AnythingLLM")
        print(f"  Available: {[w['slug'] for w in workspaces]}")
        sys.exit(1)

    ws = matched[0]
    print(f"Ingesting into workspace: {ws['name']} (slug={ws['slug']})")
    uploaded = []
    skipped = []

    for rel_path in files:
        full_path = os.path.join(DOCS_ROOT, rel_path)
        if not os.path.exists(full_path):
            print(f"  SKIP  {rel_path} (not found at {full_path})")
            skipped.append(rel_path)
            continue

        with open(full_path, encoding="utf-8") as f:
            content = f.read()

        title = os.path.basename(rel_path).replace(".md", "")
        result = upload_raw_text(title, content, ws["slug"])
        if result.get("success") is True:
            print(f"  OK    {rel_path}")
            uploaded.append(rel_path)
        else:
            print(f"  FAIL  {rel_path}: {result.get('error', result)}")


    print(f"\nDone: {len(uploaded)} uploaded, {len(skipped)} skipped")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", help="Workspace slug to ingest into (engineering|roadmap)")
    parser.add_argument("--list", action="store_true", help="List existing documents")
    args = parser.parse_args()

    if args.list:
        list_documents()
    elif args.workspace:
        ingest_workspace(args.workspace)
    else:
        parser.print_help()
