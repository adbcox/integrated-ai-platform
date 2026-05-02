#!/usr/bin/env bash
# D-17-04 WP-17-04-04 — provision low-privilege iap-sync user and rotate
# its API token into Vault, replacing the admin-scoped token from T1.7.
#
# Doctrine (per docker/openproject/README.md "Connector authoring prerequisites"):
#   1. iap-sync user gets a custom role with only WP CRUD + version
#      create + custom-field read/write
#   2. The user is added as a member of the 'roadmap' project with that role
#   3. Reset/regenerate the user's API key, capture, store at
#      secret/openproject/api#token (replaces the admin token)
#   4. Reset the admin user's API key (regenerate; we do NOT store it)
#      so the broad-scope token from T1.7 stops floating
#
# Idempotent: if iap-sync exists with a valid token in Vault, exit 0.
#
# Hash-only verification: token never displayed; sha256[12] only.
#
# Run on Mac Mini.

set -euo pipefail

DOCKER=/opt/homebrew/bin/docker
CONTAINER=openproject
IAP_SYNC_LOGIN="iap-sync"
IAP_SYNC_EMAIL="iap-sync@local.dev"
IAP_SYNC_FIRST="IAP"
IAP_SYNC_LAST="Sync"
ROLE_NAME="IAP Sync"
PROJECT_IDENT="roadmap"
SECRET_PATH="secret/openproject/api"   # pragma: allowlist secret
VERIFY_URL="http://192.168.10.145:8086/api/v3/users/me"

source "$(dirname "$0")/lib/vault-admin-token.sh"
VAULT_TOKEN=$(resolve_admin_vault_token) || exit 2

log() { printf '[mint-iap-sync] %s\n' "$*" >&2; }
sha256_prefix() { /usr/bin/shasum -a 256 | /usr/bin/awk '{print substr($1,1,12)}'; }

verify_token() {
    local token="$1"
    local b64=$(printf 'apikey:%s' "$token" | /usr/bin/base64)
    local code
    code=$(printf 'header = "Authorization: Basic %s"\n' "$b64" \
        | /usr/bin/curl -sS -o /dev/null -w '%{http_code}' \
            --config - "$VERIFY_URL" || true)
    [ "$code" = "200" ]
}

# ── Step 1: idempotency check ─────────────────────────────────────────
log "step 1: checking existing token in Vault"
EXISTING=$(${DOCKER} exec -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server \
    vault kv get -field=token "${SECRET_PATH}" 2>/dev/null || true)

if [ -n "${EXISTING}" ] && verify_token "${EXISTING}"; then
    EXISTING_LOGIN=$(printf 'header = "Authorization: Basic %s"\n' "$(printf 'apikey:%s' "${EXISTING}" | /usr/bin/base64)" \
        | /usr/bin/curl -sS --config - "${VERIFY_URL}" \
        | /usr/bin/python3 -c "import json,sys; print(json.load(sys.stdin).get('login',''))")
    if [ "${EXISTING_LOGIN}" = "${IAP_SYNC_LOGIN}" ]; then
        log "  ✅ existing token is iap-sync's; sha256[12]=$(printf '%s' "${EXISTING}" | sha256_prefix)"
        log "  no action required (idempotent exit)"
        unset EXISTING
        exit 0
    fi
    log "  existing token belongs to '${EXISTING_LOGIN}', not iap-sync — will rotate"
fi
unset EXISTING

# ── Step 2: create user + role + membership + reset key via Rails ─────
log "step 2: provisioning iap-sync user, role, membership, and minting token"

PROVISION_RUBY=$(cat <<'RUBY'
TOKEN_SENTINEL_BEGIN = "__IAP_TOKEN_BEGIN__"
TOKEN_SENTINEL_END   = "__IAP_TOKEN_END__"

login        = "iap-sync"
email        = "iap-sync@local.dev"
first_name   = "IAP"
last_name    = "Sync"
role_name    = "IAP Sync"
project_id   = "roadmap"

begin
  # ── Role ─────────────────────────────────────────────────────────
  role = ProjectRole.find_by(name: role_name) || ProjectRole.new(name: role_name)
  if role.new_record?
    role.permissions = [
      :view_work_packages,
      :add_work_packages,
      :edit_work_packages,
      :delete_work_packages,
      :manage_subtasks,
      :assign_versions,
      :view_categories,
      :manage_categories,
      :view_versions,
      :manage_versions,
    ]
    role.save!
    STDERR.puts "  created role: #{role.name} id=#{role.id}"
  else
    STDERR.puts "  role exists: #{role.name} id=#{role.id}"
  end

  # ── User ─────────────────────────────────────────────────────────
  user = User.find_by(login: login)
  if user.nil?
    user = User.new(
      login:      login,
      mail:       email,
      firstname:  first_name,
      lastname:   last_name,
      admin:      false,
      status:     User.statuses[:active],
      language:   "en",
    )
    user.password = SecureRandom.hex(32)
    user.password_confirmation = user.password
    user.save!
    STDERR.puts "  created user: #{user.login} id=#{user.id}"
  else
    STDERR.puts "  user exists: #{user.login} id=#{user.id}"
  end

  # ── Membership ───────────────────────────────────────────────────
  project = Project.find_by(identifier: project_id)
  raise "project '#{project_id}' missing — run WP-17-04-03 import first" unless project

  existing_member = Member.where(project: project, user_id: user.id).first
  if existing_member
    unless existing_member.roles.include?(role)
      existing_member.roles << role
      STDERR.puts "  added role to existing membership"
    else
      STDERR.puts "  membership + role already in place"
    end
  else
    Member.create!(project: project, principal: user, roles: [role])
    STDERR.puts "  created membership: user=#{user.login} project=#{project.identifier} role=#{role.name}"
  end

  # ── Project module: work_package_tracking must be enabled or all WP
  #    permission checks evaluate to false on the API side. ───────
  unless project.enabled_module_names.include?("work_package_tracking")
    project.enabled_module_names = (project.enabled_module_names + ["work_package_tracking"]).uniq
    project.save!
    STDERR.puts "  enabled work_package_tracking module on #{project.identifier}"
  end

  # ── Workflows: needed for two reasons.
  #    1. /api/v3/statuses returns 403 if the role has zero workflow
  #       rows (regardless of granted permissions).
  #    2. The sync needs to PATCH WPs to land in {New, In progress,
  #       Closed, On hold, Rejected} from arbitrary current states.
  #    Strategy: clone Member's transitions for breadth, then add
  #    explicit '*→{sync target}' on every type+status combo.
  Workflow.where(role_id: role.id).delete_all
  source_role = ProjectRole.find_by(name: "Member")
  cloned = 0
  if source_role
    Workflow.where(role_id: source_role.id).find_each do |w|
      Workflow.create!(
        role_id:        role.id,
        type_id:        w.type_id,
        old_status_id:  w.old_status_id,
        new_status_id:  w.new_status_id,
        author:         w.author,
        assignee:       w.assignee,
      )
      cloned += 1
    end
    STDERR.puts "  cloned #{cloned} workflow transitions from Member -> IAP Sync"
  end
  target_status_ids = Status.where(name: ["New","In progress","Closed","On hold","Rejected"]).pluck(:id)
  added = 0
  Type.pluck(:id).each do |tid|
    Status.pluck(:id).each do |from_id|
      target_status_ids.each do |to_id|
        next if from_id == to_id
        next if Workflow.where(role_id: role.id, type_id: tid,
                                old_status_id: from_id, new_status_id: to_id).exists?
        Workflow.create!(role_id: role.id, type_id: tid,
                          old_status_id: from_id, new_status_id: to_id)
        added += 1
      end
    end
  end
  STDERR.puts "  added #{added} explicit '*-> sync target' transitions; total #{Workflow.where(role_id: role.id).count}"

  # ── Reset API key (returns plaintext only at reset time) ─────────
  Token::API.where(user_id: user.id).destroy_all
  result = APITokens::CreateService.new(user: user).call(token_name: "iap-sync-vault-#{Time.now.utc.strftime('%Y%m%d%H%M%S')}")
  raise "API token reset failed: #{result.errors.full_messages.join('; ')}" unless result.success?
  plain = result.result.plain_value
  raise "plain_value empty" if plain.nil? || plain.empty?

  STDOUT.write("#{TOKEN_SENTINEL_BEGIN}#{plain}#{TOKEN_SENTINEL_END}")
rescue => e
  STDERR.puts "ERROR: #{e.class}: #{e.message}"
  STDERR.puts e.backtrace.first(5).join("\n")
  exit 5
end
RUBY
)

RAW_OUT=$(${DOCKER} exec "${CONTAINER}" \
    sh -c 'set -a && . /vault/secrets/credentials.env && set +a && exec bundle exec rails runner "$1"' \
    -- "${PROVISION_RUBY}" 2>/tmp/iap-sync-err.$$) || {
    log "❌ rails runner failed (exit $?). stderr:"
    /bin/cat /tmp/iap-sync-err.$$ >&2 || true
    /bin/rm -f /tmp/iap-sync-err.$$
    exit 6
}
/bin/cat /tmp/iap-sync-err.$$ >&2  # progress lines from STDERR.puts
/bin/rm -f /tmp/iap-sync-err.$$

NEW_TOKEN=$(printf '%s' "${RAW_OUT}" | /usr/bin/sed -n 's/.*__IAP_TOKEN_BEGIN__\(.*\)__IAP_TOKEN_END__.*/\1/p')
unset RAW_OUT

if [ -z "${NEW_TOKEN}" ]; then
    log "❌ no token between sentinels"
    exit 7
fi

NEW_HASH=$(printf '%s' "${NEW_TOKEN}" | sha256_prefix)
log "  ✅ iap-sync token minted; sha256[12]=${NEW_HASH}"

# ── Step 3: rotate into Vault ─────────────────────────────────────────
log "step 3: rotating into ${SECRET_PATH}#token"
printf '%s' "${NEW_TOKEN}" | ${DOCKER} exec -i \
    -e VAULT_TOKEN="${VAULT_TOKEN}" \
    vault-server \
    sh -c "vault kv patch ${SECRET_PATH} token=- >/dev/null"

# ── Step 4: verify ────────────────────────────────────────────────────
log "step 4: verifying iap-sync token against ${VERIFY_URL}"
if verify_token "${NEW_TOKEN}"; then
    log "  ✅ /api/v3/users/me returned 200 — iap-sync token live"
else
    log "  ❌ verification failed"
    unset NEW_TOKEN
    exit 8
fi
unset NEW_TOKEN

# ── Step 5: regenerate admin's API key (do NOT store) ─────────────────
log "step 5: regenerating admin API key (rotating away the T1.7 admin token)"
ADMIN_RESET_RUBY=$(cat <<'RUBY'
admin = User.where(admin: true).order(:id).first
killed = Token::API.where(user_id: admin.id).destroy_all
STDERR.puts "  destroyed #{killed.size} admin API token(s) — admin must re-mint via T1.7 if needed"
RUBY
)
${DOCKER} exec "${CONTAINER}" \
    sh -c 'set -a && . /vault/secrets/credentials.env && set +a && exec bundle exec rails runner "$1"' \
    -- "${ADMIN_RESET_RUBY}" 2>&1 | /usr/bin/grep -v "Increasing database pool" >&2

log "WP-17-04-04 prerequisite complete:"
log "  - iap-sync user provisioned with low-priv 'IAP Sync' role"
log "  - secret/openproject/api#token now holds iap-sync's user-scoped token"
log "  - admin API token destroyed (re-mint via openproject-mint-admin-token.sh if needed)"
