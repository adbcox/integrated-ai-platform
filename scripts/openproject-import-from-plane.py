#!/usr/bin/env python3
# HISTORICAL MIGRATION SCRIPT.
# Do not use for new work. Retained to preserve the one-time Plane->OpenProject
# import mapping chain (D-17-04 WP-17-04-03).
#
"""
D-17-04 WP-17-04-03 — Import Plane snapshot into OpenProject.

Reads docs/_archive/plane-export-YYYY-MM-DD.json (produced by
scripts/plane-final-snapshot.sh) and creates the matching
OpenProject project, custom field, categories, versions, and work
packages via Rails console (not REST — REST requires per-project
permission grants we'd have to bootstrap; Rails runner is admin-direct).

Mapping (codified):

  Plane state         → OpenProject status
  ─────────────────────────────────────────
  Backlog             → New (default)
  Todo                → To be scheduled
  Ready               → Scheduled
  In Progress         → In progress
  In Review           → In testing
  Testing             → In testing
  Done                → Closed
  Cancelled           → Rejected
  Deferred            → On hold

  Plane priority      → OpenProject priority
  ─────────────────────────────────────────
  urgent              → Immediate
  high                → High
  medium              → Normal
  low                 → Low
  none                → Normal (default)

  Plane labels        → OpenProject categories (project-scoped)
  Plane modules       → OpenProject versions (Phase-17, etc.)
  Plane cycles        → OpenProject versions (Sprint 1..N)
  Plane sequence_id   → OpenProject custom field "Plane RM ID" (RM-#)

Idempotent: if the project "Roadmap" exists with WP count > 0, refuses
to re-run unless --force is passed (forces a destroy + re-create).

Run on Mac Mini.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXPORT_PATH = REPO_ROOT / "docs" / "_archive" / "plane-export-2026-05-02.json"

DOCKER = "/opt/homebrew/bin/docker"
CONTAINER = "openproject"

# Codified mappings — source of truth for WP-17-04-03
STATE_MAP = {
    "Backlog":     "New",
    "Todo":        "To be scheduled",
    "Ready":       "Scheduled",
    "In Progress": "In progress",
    "In Review":   "In testing",
    "Testing":     "In testing",
    "Done":        "Closed",
    "Cancelled":   "Rejected",
    "Deferred":    "On hold",
}

PRIORITY_MAP = {
    "urgent": "Immediate",
    "high":   "High",
    "medium": "Normal",
    "low":    "Low",
    "none":   "Normal",
    None:     "Normal",
}


def build_payload(export_path: Path) -> dict:
    """Read Plane export and project it into the import-payload shape."""
    with export_path.open() as f:
        plane = json.load(f)

    state_by_id = {s["id"]: s["name"] for s in plane["states"]}
    label_by_id = {l["id"]: l["name"] for l in plane["labels"]}
    module_by_id = {m["id"]: m["name"] for m in plane["modules"]}
    cycle_by_id = {c["id"]: c["name"] for c in plane["cycles"]}

    # Issue → module/cycle membership lives on the join tables, which the
    # Plane API surfaces only via separate endpoints we didn't capture.
    # WP-04 (connector rewrite) will re-derive these from the live source
    # of truth (PROJECT_FRAMEWORK.md). For the snapshot import we set
    # version=Phase-17 if the title starts with "[17." or "[D-17-",
    # otherwise null — sufficient for visual hierarchy in OpenProject.
    def infer_version(title: str) -> str | None:
        for tag, version in [
            ("[17.", "Phase-17"),
            ("[D-17-", "Phase-17"),
            ("[16.", "Phase-16"),
            ("[D-16-", "Phase-16"),
            ("[15.", "Phase-15"),
            ("[D-15-", "Phase-15"),
        ]:
            if title.startswith(tag):
                return version
        return None

    issues_out = []
    for issue in plane["issues"]:
        plane_state = state_by_id.get(issue["state"])
        op_status = STATE_MAP.get(plane_state, "New")

        plane_priority = issue.get("priority")
        op_priority = PRIORITY_MAP.get(plane_priority, "Normal")

        labels_resolved = [
            label_by_id[lid] for lid in issue.get("labels", [])
            if lid in label_by_id
        ]

        title = issue["name"]
        issues_out.append({
            "plane_id": issue["id"],
            "plane_seq": issue["sequence_id"],
            "title": title[:255],
            "description": issue.get("description_html") or "",
            "status_name": op_status,
            "priority_name": op_priority,
            "labels": labels_resolved,
            "version_name": infer_version(title),
            "start_date": issue.get("start_date"),
            "due_date": issue.get("target_date"),
            "created_at": issue["created_at"],
        })

    payload = {
        "project": {
            "name": "Roadmap",
            "identifier": "roadmap",
            "description": "Migrated from Plane CE 2026-05-02 (D-17-04 WP-17-04-03). "
                           "Source of truth: docs/PROJECT_FRAMEWORK.md.",
        },
        "categories": sorted(set(label_by_id.values())),
        "versions":   sorted(set(module_by_id.values()) | set(cycle_by_id.values())),
        "issues":     issues_out,
    }
    return payload


# Ruby script that runs inside the openproject container.
# Receives the JSON payload via STDIN; emits sentinel-bracketed JSON
# summary to STDOUT.
RUBY_IMPORTER = r"""
require "json"

SENTINEL_BEGIN = "__IMPORT_BEGIN__"
SENTINEL_END   = "__IMPORT_END__"

def log(msg) = STDERR.puts("[import] #{msg}")

payload = JSON.parse(STDIN.read)
admin = User.where(admin: true).order(:id).first
raise "no admin user" unless admin

User.current = admin

# ── Project ─────────────────────────────────────────────────────────
identifier = payload["project"]["identifier"]
existing = Project.find_by(identifier: identifier)
if existing
  if ARGV.include?("--force")
    log "destroying existing project #{identifier} (--force)"
    existing.destroy!
    existing = nil
  elsif existing.work_packages.count.positive?
    raise "project #{identifier} already has #{existing.work_packages.count} WPs; pass --force to wipe"
  end
end

project = existing || Project.new(
  name:        payload["project"]["name"],
  identifier:  identifier,
  description: payload["project"]["description"],
  public:      false,
)
project.save!
log "project ready: id=#{project.id} identifier=#{project.identifier}"

# Activate ALL types for this project (so we can use Task by default
# but operator can change to Feature/Bug/etc later)
project.types = Type.all
project.save!

# Activate ALL statuses for the workflow (otherwise WP creation rejects
# any non-default status as "invalid transition")
default_type = Type.where(is_default: true, is_milestone: false).order(:position).first
default_status = Status.where(is_default: true).first
all_role = Role.where(builtin: 0).order(:position).first || Role.first

# Create permissive workflows: from default_status to ANY status, on ALL types,
# for the standard role. This avoids "Invalid transition" errors during bulk
# import of issues that were created in arbitrary states in Plane.
Workflow.where(role: all_role).delete_all
Type.all.each do |t|
  Status.all.each do |s|
    next if s == default_status
    Workflow.create!(role: all_role, type: t, old_status: default_status, new_status: s)
    Workflow.create!(role: all_role, type: t, old_status: s, new_status: default_status)
  end
end
log "workflows: created permissive default<->any for role=#{all_role.name}"

# ── Custom field for Plane RM ID ────────────────────────────────────
cf_name = "Plane RM ID"
cf = WorkPackageCustomField.find_by(name: cf_name) || WorkPackageCustomField.create!(
  name: cf_name,
  field_format: "string",
  is_required: false,
  is_filter: true,
  searchable: true,
)
project.work_package_custom_fields << cf unless project.work_package_custom_fields.include?(cf)
Type.all.each { |t| t.custom_fields << cf unless t.custom_fields.include?(cf) }
log "custom field ready: #{cf.name} id=#{cf.id}"

# ── Categories ──────────────────────────────────────────────────────
cat_name_to_id = {}
payload["categories"].each do |name|
  cat = project.categories.find_or_create_by!(name: name[0, 30])
  cat_name_to_id[name] = cat.id
end
log "categories: #{cat_name_to_id.size} ready"

# ── Versions ────────────────────────────────────────────────────────
ver_name_to_id = {}
payload["versions"].each do |name|
  v = project.versions.find_or_create_by!(name: name[0, 60])
  ver_name_to_id[name] = v.id
end
log "versions: #{ver_name_to_id.size} ready"

# ── Issues → WorkPackages ───────────────────────────────────────────
status_by_name   = Status.all.index_by(&:name)
priority_by_name = IssuePriority.all.index_by(&:name)

created = 0
errors  = []

def safe_date(s)
  return nil if s.nil? || s.empty?
  Date.parse(s) rescue nil
end

payload["issues"].each_with_index do |issue, idx|
  status   = status_by_name[issue["status_name"]]   || status_by_name["New"]
  priority = priority_by_name[issue["priority_name"]] || priority_by_name["Normal"]
  cat_id   = (issue["labels"] || []).map { |l| cat_name_to_id[l] }.compact.first
  ver_id   = ver_name_to_id[issue["version_name"]]

  wp = WorkPackage.new(
    project:     project,
    type:        default_type,
    subject:     issue["title"],
    description: issue["description"],
    status:      status,
    priority:    priority,
    author:      admin,
    category_id: cat_id,
    version_id:  ver_id,
    start_date:  safe_date(issue["start_date"]),
    due_date:    safe_date(issue["due_date"]),
  )
  wp.custom_field_values = { cf.id => "RM-#{issue['plane_seq']}" }
  if wp.save
    created += 1
  else
    errors << { seq: issue["plane_seq"], errors: wp.errors.full_messages }
  end

  STDERR.print "\r[import] WPs: #{created}/#{idx + 1}" if (idx + 1) % 50 == 0
end
STDERR.puts ""

summary = {
  project_id:       project.id,
  project_name:     project.name,
  categories_count: cat_name_to_id.size,
  versions_count:   ver_name_to_id.size,
  custom_field_id:  cf.id,
  issues_total:     payload["issues"].size,
  issues_created:   created,
  errors_count:     errors.size,
  errors_sample:    errors.first(10),
}
STDOUT.write("#{SENTINEL_BEGIN}#{summary.to_json}#{SENTINEL_END}")
"""


def run_import(payload: dict, force: bool) -> dict:
    """Stream payload to Rails runner and parse the sentinel-bracketed result."""
    payload_json = json.dumps(payload)
    extra = ["--force"] if force else []

    # `rails runner` reads the script from argv. Payload goes via STDIN.
    cmd = [
        DOCKER, "exec", "-i", CONTAINER,
        "sh", "-c",
        'set -a && . /vault/secrets/credentials.env && set +a && '
        'exec bundle exec rails runner "$1" -- "$@"',
        "--", RUBY_IMPORTER, *extra,
    ]
    result = subprocess.run(
        cmd, input=payload_json, capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        sys.stderr.write("=== Rails runner stderr ===\n")
        sys.stderr.write(result.stderr)
        sys.stderr.write("\n=== Rails runner stdout (head) ===\n")
        sys.stderr.write(result.stdout[:2000])
        raise SystemExit(f"rails runner exited {result.returncode}")

    sys.stderr.write(result.stderr)  # progress lines

    # Extract sentinel-bracketed JSON from stdout (boot logs may precede it)
    out = result.stdout
    begin = out.find("__IMPORT_BEGIN__")
    end = out.find("__IMPORT_END__")
    if begin < 0 or end < 0:
        raise SystemExit(f"no sentinel in stdout (head 500 chars):\n{out[:500]}")
    return json.loads(out[begin + len("__IMPORT_BEGIN__"):end])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true",
                    help="destroy existing 'roadmap' project first")
    ap.add_argument("--export-path", type=Path, default=EXPORT_PATH)
    args = ap.parse_args()

    if not args.export_path.is_file():
        sys.exit(f"export not found: {args.export_path}")

    print(f"reading {args.export_path}")
    payload = build_payload(args.export_path)
    print(f"  project:   {payload['project']['name']} ({payload['project']['identifier']})")
    print(f"  categories: {len(payload['categories'])}")
    print(f"  versions:   {len(payload['versions'])}")
    print(f"  issues:     {len(payload['issues'])}")
    print()

    print("running rails import…")
    summary = run_import(payload, force=args.force)
    print()
    print("=== import complete ===")
    print(json.dumps(summary, indent=2))
    return 0 if summary["errors_count"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
