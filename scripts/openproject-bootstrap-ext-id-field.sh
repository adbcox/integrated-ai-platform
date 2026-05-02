#!/usr/bin/env bash
# D-17-04 WP-17-04-04 — bootstrap "External ID" custom field on WorkPackage,
# enable it on Type=Task across the project, and backfill values by
# parsing the canonical `[D-NN-XX]` / `[Phase-NN]` / `[NN.X]` prefix
# already present in WP subjects (placed there by WP-17-04-03 import).
#
# Idempotent. Safe to re-run.
#
# Run on Mac Mini.

set -euo pipefail

DOCKER=/opt/homebrew/bin/docker
CONTAINER=openproject

log() { printf '[bootstrap-ext-id] %s\n' "$*" >&2; }

BOOTSTRAP_RUBY=$(cat <<'RUBY'
User.current = User.where(admin: true).order(:id).first

# ── 1. Custom field ───────────────────────────────────────────────
cf = WorkPackageCustomField.find_by(name: "External ID")
if cf.nil?
  cf = WorkPackageCustomField.create!(
    name:                  "External ID",
    field_format:          "string",
    is_required:           false,
    searchable:            true,
    is_for_all:            true,    # auto-enable on all WP types
    is_filter:             true,
  )
  STDERR.puts "  created CF id=#{cf.id} name='External ID'"
else
  STDERR.puts "  CF exists id=#{cf.id}"
  unless cf.is_for_all?
    cf.update!(is_for_all: true)
    STDERR.puts "  flipped is_for_all=true"
  end
end

# ── 2. Enable on the roadmap project explicitly (belt+braces) ─────
proj = Project.find_by(identifier: "roadmap")
if proj
  unless proj.work_package_custom_fields.include?(cf)
    proj.work_package_custom_fields << cf
    proj.save!
    STDERR.puts "  enabled CF on project=#{proj.identifier}"
  else
    STDERR.puts "  CF already enabled on project=#{proj.identifier}"
  end
end

# ── 3. Make sure every Type has the CF ────────────────────────────
Type.find_each do |t|
  unless t.custom_fields.include?(cf)
    t.custom_fields << cf
    t.save!
    STDERR.puts "  enabled CF on type=#{t.name}"
  end
end

# ── 4. Backfill — parse "[X] subject" prefix ─────────────────────
PREFIX_RE = /\A\[([^\]]+)\]\s*/
filled = 0
skipped = 0
WorkPackage.where(project: proj).reorder(nil).find_each do |wp|
  m = wp.subject.match(PREFIX_RE)
  unless m
    skipped += 1
    next
  end
  ext = m[1].strip
  current = wp.send("custom_field_#{cf.id}")
  if current == ext
    skipped += 1
    next
  end
  wp.send("custom_field_#{cf.id}=", ext)
  if wp.save(validate: false)  # bypass workflow gates on bulk backfill
    filled += 1
  else
    STDERR.puts "  WARN ##{wp.id} save failed: #{wp.errors.full_messages.join('; ')}"
  end
end
STDERR.puts "  backfill complete: filled=#{filled} skipped=#{skipped}"

# ── 5. Verification — count distinct ext IDs ──────────────────────
distinct = WorkPackage.where(project: proj).reorder(nil)
  .joins(:custom_values).where(custom_values: {custom_field_id: cf.id})
  .where.not(custom_values: {value: nil}).where.not(custom_values: {value: ""})
  .distinct.count
STDERR.puts "  WPs with non-empty External ID: #{distinct}"
RUBY
)

${DOCKER} exec "${CONTAINER}" \
    sh -c 'set -a && . /vault/secrets/credentials.env && set +a && exec bundle exec rails runner "$1"' \
    -- "${BOOTSTRAP_RUBY}" 2>&1 | /usr/bin/grep -v "Increasing database pool"

log "External ID custom field bootstrap complete"
