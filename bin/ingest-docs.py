#!/usr/bin/env python3
"""
ingest-docs.py — Upload platform docs into AnythingLLM workspaces

Usage:
    python3 bin/ingest-docs.py --workspace engineering
    python3 bin/ingest-docs.py --workspace roadmap
    python3 bin/ingest-docs.py --files path/to/file.md [path/to/other.md ...]
    python3 bin/ingest-docs.py --dir docs/roadmap/ITEMS --workspace roadmap
    python3 bin/ingest-docs.py --list
    python3 bin/ingest-docs.py --list-workspace engineering

Exit codes: 0=success  1=failures  2=script error
"""

import argparse
import json
import os
import re
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


# ── Metadata extraction ────────────────────────────────────────────────────────

def extract_yaml_frontmatter(content):
    """Extract YAML frontmatter between --- delimiters."""
    match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    if not match:
        return {}, content
    body = content[match.end():]
    fields = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            fields[k.strip()] = v.strip().strip('"').strip("'")
    return fields, body


def extract_markdown_metadata(content):
    """
    Extract metadata from roadmap-item markdown list format:
        - **ID:** `RM-AI-001`
        - **Category:** `AI`
    Returns dict of extracted fields and original content unchanged.
    """
    pattern = re.compile(r"^- \*\*([^*:]+):?\*\*\s*`?([^`\n]+?)`?\s*$", re.MULTILINE)
    fields = {}
    for m in pattern.finditer(content):
        key = m.group(1).strip().rstrip(":")
        val = m.group(2).strip()
        fields[key.lower().replace(" ", "_")] = val
    return fields


def build_context_block(rel_path, yaml_fm, md_meta):
    """
    Build a [DOCUMENT CONTEXT] header prepended to the embedded content.
    Combines path info, YAML frontmatter, and markdown metadata.
    """
    parts = rel_path.replace("\\", "/").split("/")
    directory = "/".join(parts[:-1]) if len(parts) > 1 else "docs"
    filename = parts[-1]

    lines = [
        "[DOCUMENT CONTEXT]",
        f"file: {rel_path}",
        f"directory: {directory}",
        f"filename: {filename}",
    ]

    # YAML frontmatter fields
    for key in ("id", "category", "priority", "status", "phase", "type", "title"):
        val = yaml_fm.get(key)
        if val:
            lines.append(f"{key}: {val}")

    # Markdown metadata fields (roadmap items)
    md_map = {
        "id": "id",
        "title": "title",
        "category": "category",
        "type": "type",
        "status": "status",
        "priority_class": "priority_class",
        "priority": "priority",
        "target_horizon": "target_horizon",
        "loe": "loe",
        "maturity": "maturity",
    }
    for md_key, label in md_map.items():
        if md_key in md_meta and label not in [l.split(":")[0] for l in lines]:
            lines.append(f"{label}: {md_meta[md_key]}")

    lines.append("[END CONTEXT]")
    return "\n".join(lines)


def enrich_content(rel_path, raw_content):
    """
    Extract any metadata and prepend structured context block.
    Returns (context_block_dict, enriched_content_string).
    """
    yaml_fm, body = extract_yaml_frontmatter(raw_content)
    md_meta = extract_markdown_metadata(raw_content)

    context_block = build_context_block(rel_path, yaml_fm, md_meta)
    enriched = f"{context_block}\n\n{raw_content}"
    return yaml_fm, md_meta, enriched


# ── API helpers ────────────────────────────────────────────────────────────────

def api(method, path, body=None):
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.read().decode()[:300]}"}
    except Exception as e:
        return {"error": str(e)}


def upload_file(rel_path, content, workspace_slug=None):
    """
    Upload one file with enriched content and structured metadata.
    rel_path is relative to DOCS_ROOT (e.g. "roadmap/ITEMS/RM-AI-001.md").
    """
    parts = rel_path.replace("\\", "/").split("/")
    directory = "/".join(parts[:-1]) if len(parts) > 1 else "docs"

    # Title = full path without extension, with > separators for readability
    title = rel_path.replace(".md", "").replace("/", " > ")

    yaml_fm, md_meta, enriched = enrich_content(rel_path, content)

    # docSource encodes directory for grouping
    doc_source = directory if directory else "docs"

    body = {
        "textContent": enriched,
        "metadata": {
            "title": title,
            "docSource": doc_source,
            "docAuthor": yaml_fm.get("author") or md_meta.get("author", "platform-docs"),
            "description": (
                yaml_fm.get("description")
                or md_meta.get("title")
                or ""
            ),
        },
        # Do NOT pass addToWorkspaces here — workspace association and embedding
        # are handled separately via update-embeddings to avoid double-ingestion.
        "addToWorkspaces": "",
    }
    return api("POST", "/api/v1/document/raw-text", body)


def get_or_create_workspace(name):
    """Return workspace dict, creating it if it doesn't exist."""
    workspaces = api("GET", "/api/v1/workspaces").get("workspaces", [])
    slug_prefix = name.lower().replace(" ", "-").replace("_", "-")
    matched = [w for w in workspaces if w["slug"] == slug_prefix or w["slug"].startswith(slug_prefix)]
    if matched:
        return matched[0]
    result = api("POST", "/api/v1/workspace/new", {"name": name})
    return result.get("workspace", {})


def embed_docs_in_workspace(ws_slug, doc_paths, batch_size=50):
    """Call update-embeddings in batches to avoid Prisma transaction timeouts."""
    adds = [f"custom-documents/{p}" for p in doc_paths]
    total = 0
    batches = [adds[i:i + batch_size] for i in range(0, len(adds), batch_size)]
    for i, batch in enumerate(batches, 1):
        result = api(
            "POST",
            f"/api/v1/workspace/{ws_slug}/update-embeddings",
            {"adds": batch, "deletes": []},
        )
        ws = result.get("workspace", {})
        if isinstance(ws, list):
            ws = ws[0] if ws else {}
        total = len(ws.get("documents", []))
        print(f"  Batch {i}/{len(batches)}: workspace now has {total} docs")
    return total


# ── Commands ───────────────────────────────────────────────────────────────────

def cmd_list_documents():
    result = api("GET", "/api/v1/documents")
    items = result.get("localFiles", {}).get("items", [])
    count = sum(len(folder.get("items", [])) for folder in items)
    print(f"Documents in AnythingLLM: {count}")
    for folder in items:
        for doc in folder.get("items", []):
            print(f"  {doc.get('name', '?')}")


def cmd_list_workspace(workspace_slug):
    workspaces = api("GET", "/api/v1/workspaces").get("workspaces", [])
    matched = [w for w in workspaces if workspace_slug in w["slug"]]
    if not matched:
        print(f"Workspace not found: {workspace_slug}")
        return
    ws = matched[0]
    docs = ws.get("documents", [])
    print(f"Workspace '{ws['name']}' ({ws['slug']}): {len(docs)} documents")
    for doc in sorted(docs, key=lambda x: x.get("docpath", "")):
        print(f"  {doc.get('docpath', '?')}")


def _ingest_file_list(files, workspace_slug, show_context=False):
    """Core loop: upload files, collect locations, embed."""
    ws = get_or_create_workspace(workspace_slug)
    if not ws:
        print(f"ERROR: could not find/create workspace '{workspace_slug}'")
        sys.exit(2)
    print(f"Workspace: {ws['name']} (slug={ws['slug']})")

    uploaded_locations = []
    failed = []
    skipped = []

    for rel_path, full_path in files:
        if not os.path.exists(full_path):
            print(f"  SKIP  {rel_path}")
            skipped.append(rel_path)
            continue

        with open(full_path, encoding="utf-8") as f:
            content = f.read()

        result = upload_file(rel_path, content, ws["slug"])
        if result.get("success") is True:
            docs = result.get("documents", [])
            if docs:
                loc = docs[0].get("location", "")
                fname = loc.replace("custom-documents/", "") if loc else ""
                uploaded_locations.append(fname)
                if show_context:
                    _, md_meta, _ = enrich_content(rel_path, content)
                    parts = rel_path.split("/")
                    directory = "/".join(parts[:-1])
                    cat = md_meta.get("category", yaml_fields_from(content).get("category", "—"))
                    status = md_meta.get("status", yaml_fields_from(content).get("status", "—"))
                    print(f"  OK    {rel_path}  [dir={directory} cat={cat} status={status}]")
                else:
                    print(f"  OK    {rel_path}")
            else:
                print(f"  OK    {rel_path} (no location returned)")
        else:
            print(f"  FAIL  {rel_path}: {result.get('error', result)}")
            failed.append(rel_path)

    print(f"\nUploaded: {len(uploaded_locations)}  Failed: {len(failed)}  Skipped: {len(skipped)}")

    if uploaded_locations:
        print("Triggering embedding...")
        doc_count = embed_docs_in_workspace(ws["slug"], uploaded_locations)
        print(f"Workspace now has {doc_count} embedded documents")

    return len(failed) == 0


def yaml_fields_from(content):
    fm, _ = extract_yaml_frontmatter(content)
    return fm


def cmd_ingest_workspace(workspace_slug):
    file_list = WORKSPACE_DOCS.get(workspace_slug)
    if not file_list:
        print(f"ERROR: unknown preset workspace '{workspace_slug}'. Valid: {list(WORKSPACE_DOCS.keys())}")
        sys.exit(2)
    files = [(rel, os.path.join(DOCS_ROOT, rel)) for rel in file_list]
    success = _ingest_file_list(files, workspace_slug, show_context=True)
    sys.exit(0 if success else 1)


def cmd_ingest_files(rel_paths, workspace_slug):
    files = [(rel, os.path.join(DOCS_ROOT, rel)) for rel in rel_paths]
    success = _ingest_file_list(files, workspace_slug, show_context=True)
    sys.exit(0 if success else 1)


def cmd_ingest_dir(directory, workspace_slug, recursive=True, pattern="*.md"):
    """Ingest all markdown files from a directory."""
    import fnmatch
    base = os.path.join(DOCS_ROOT, directory)
    if not os.path.isdir(base):
        print(f"ERROR: directory not found: {base}")
        sys.exit(2)

    files = []
    for root, dirs, fnames in os.walk(base):
        dirs.sort()
        for fname in sorted(fnames):
            if fnmatch.fnmatch(fname, pattern):
                full = os.path.join(root, fname)
                rel = os.path.relpath(full, DOCS_ROOT).replace("\\", "/")
                files.append((rel, full))
        if not recursive:
            break

    print(f"Found {len(files)} files in {directory}")
    success = _ingest_file_list(files, workspace_slug, show_context=True)
    sys.exit(0 if success else 1)


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--workspace", help="Target workspace name or preset slug")
    parser.add_argument("--files", nargs="+", metavar="PATH", help="Specific files to ingest (relative to DOCS_ROOT)")
    parser.add_argument("--dir", metavar="DIR", help="Ingest all .md files under this directory (relative to DOCS_ROOT)")
    parser.add_argument("--list", action="store_true", help="List all documents in AnythingLLM")
    parser.add_argument("--list-workspace", metavar="SLUG", help="List documents in a specific workspace")
    args = parser.parse_args()

    if args.list:
        cmd_list_documents()
    elif args.list_workspace:
        cmd_list_workspace(args.list_workspace)
    elif args.dir and args.workspace:
        cmd_ingest_dir(args.dir, args.workspace)
    elif args.files and args.workspace:
        cmd_ingest_files(args.files, args.workspace)
    elif args.workspace and args.workspace in WORKSPACE_DOCS:
        cmd_ingest_workspace(args.workspace)
    else:
        parser.print_help()
        if args.workspace and args.workspace not in WORKSPACE_DOCS:
            print(f"\nNote: '{args.workspace}' is not a preset. Use --files or --dir to specify content.")
        sys.exit(2)
