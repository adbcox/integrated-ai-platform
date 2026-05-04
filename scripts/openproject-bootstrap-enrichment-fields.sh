#!/usr/bin/env bash
# D-17-55 WP-04 — bootstrap OpenProject enrichment custom fields.
# Creates/ensures WorkPackage custom fields:
#   - phase
#   - deliverable_class
#   - finding_refs
#   - dependencies
#
# Idempotent. Safe to re-run.
# Requires admin context inside openproject container (rails runner).

set -euo pipefail

DOCKER=/opt/homebrew/bin/docker
CONTAINER=openproject

log() { printf '[bootstrap-enrichment-fields] %s\n' "$*" >&2; }

BOOTSTRAP_RUBY=$(cat <<'RUBY'
User.current = User.where(admin: true).order(:id).first
raise "no admin user found" if User.current.nil?

project = Project.find_by(identifier: "roadmap")
raise "project 'roadmap' missing" if project.nil?

FIELDS = [
  { name: "phase",             field_format: "string", is_filter: true },
  { name: "deliverable_class", field_format: "string", is_filter: true },
  { name: "finding_refs",      field_format: "text",   is_filter: true },
  { name: "dependencies",      field_format: "text",   is_filter: true },
]

FIELDS.each do |cfg|
  cf = WorkPackageCustomField.find_by(name: cfg[:name])
  if cf.nil?
    cf = WorkPackageCustomField.create!(
      name: cfg[:name],
      field_format: cfg[:field_format],
      is_required: false,
      searchable: true,
      is_for_all: true,
      is_filter: cfg[:is_filter],
    )
    STDERR.puts "  created CF id=#{cf.id} name='#{cf.name}' format=#{cf.field_format}"
  else
    changed = false
    if !cf.is_for_all?
      cf.is_for_all = true
      changed = true
    end
    if !cf.searchable?
      cf.searchable = true
      changed = true
    end
    if cfg[:is_filter] && !cf.is_filter?
      cf.is_filter = true
      changed = true
    end
    cf.save! if changed
    STDERR.puts "  CF exists id=#{cf.id} name='#{cf.name}'#{changed ? ' (updated flags)' : ''}"
  end

  unless project.work_package_custom_fields.include?(cf)
    project.work_package_custom_fields << cf
    project.save!
    STDERR.puts "    enabled on project=#{project.identifier}"
  end

  Type.find_each do |t|
    unless t.custom_fields.include?(cf)
      t.custom_fields << cf
      t.save!
      STDERR.puts "    enabled on type=#{t.name}"
    end
  end
end

# Verification summary
summary = WorkPackageCustomField.where(name: FIELDS.map { |f| f[:name] }).order(:id)
summary.each do |cf|
  STDERR.puts "  verify id=#{cf.id} name='#{cf.name}' format=#{cf.field_format} is_for_all=#{cf.is_for_all}"
end
RUBY
)

${DOCKER} exec "${CONTAINER}" \
    sh -c 'set -a && . /vault/secrets/credentials.env && set +a && exec bundle exec rails runner "$1"' \
    -- "${BOOTSTRAP_RUBY}" 2>&1 | /usr/bin/grep -v "Increasing database pool"

log "enrichment field bootstrap complete"
