Phase 13 Block 4.C — Phase Plan (NetBox CMDB + Plane Label Back-fill)

Operator: claude-opus-4-7
Date: 2026-04-29
Branch posture: main, clean, in sync with origin (HEAD = 5465568,
Block 4.B addendum)
Tag baseline: v13-block-3-close at bed7d26

Pre-plan posture statements

- Doctrine acknowledged: hash-only credential verification; Vault
Agent sidecar pattern only; no .env with values; pre-commit
detect-secrets must pass without --no-verify; -orphan on token
operations; out-of-repo compose changes require pre/post snapshots;
Commit-and-Push Doctrine per phase; explicit user-approval gates at
C1 surface, C2 architecture confirmation, C3 dry-run review, C4
dry-run review, and C5 deprecation.
- Plan-first: this document is the full plan. Phase C0 and C1 are
read-only and will proceed on "approved, proceed". C2 onward stops
at the documented gates.
- Out of scope confirmed: InvenTree (4.D), cross-index service
(4.E), vision plugin (4.G), Caddy dead-route prune, Sonarr/Radarr
key rotation, M5/M4-Pro nomenclature scrub.

Note from planning window: registry consumers already include not
just topology-api and validate-cmdb.sh but docker/control-plane/
itself (mounts the YAML at /app/service-registry.yaml). That's a
third consumer C5 must migrate.

Execution-environment note

CLAUDE.md says all code execution happens on the Mac Mini at
192.168.10.145, not locally. This plan reflects that:
- Repo edits (compose files, configs, scripts, docs) are made
locally and committed from this workstation.
- Container lifecycle commands (docker compose up -d, docker
compose exec, etc.) run on the Mac Mini via ssh
admin@192.168.10.145 ....
- Vault, Caddy admin API, and Plane API calls also originate from
the Mac Mini context.

If any phase requires a step the Mac Mini cannot perform, I stop
and surface.

---

Phase C0 — Precondition verification (read-only, auto-proceed)

Verifications, all must pass:

- git status --short → empty
- git log origin/main..main → empty
- Tag v13-block-3-close resolves
- docs/phase-13/PHASE_13_BLOCK_4A_CLOSEOUT_2026-04-29.md exists,
committed
- docs/phase-13/STATE_ANCHORING_DISCOVERY_2026-04-29.md exists,
committed
- yq '.services | length' config/service-registry.yaml → 70
- ssh admin@192.168.10.145 "curl -fsSL
https://plane.internal/api/health -k" (or equivalent) → reachable
- ssh admin@192.168.10.145 "docker exec vault-server vault status
-format=json | jq .sealed" → false
- ssh admin@192.168.10.145 "curl -fsSL
http://localhost:2019/config/ | head -c 64" → Caddy admin API
responds

If anything fails I stop and surface, no auto-remediation.

Phase C1 — Architecture audit (read-only, auto-proceed)

Output: docs/phase-13/PHASE_13_BLOCK_4C_C1_AUDIT_2026-04-29.md

- C1.1 Registry analysis: enumerate the 70 services, categorize
(core platform / application / sidecar / auxiliary), map registry
fields → NetBox stock schema vs custom_fields, document
dependency-relationship modeling (NetBox interface relationships vs
cluster groups vs service-graph relationship custom field), and
note vault-path treatment (cross-reference vs custom field vs
both).
- C1.2 NetBox topology choices (decisions to confirm with user):
  - Base image: netbox-community/netbox-docker (recommended) vs
build-from-source.
  - Postgres: dedicated netbox-postgres instance (recommended for
blast-radius isolation; aligns with existing pattern where Plane
has its own DB) vs share Plane's DB.
  - Caddy hostname: netbox.internal (recommended for tool-name
clarity) vs cmdb.internal.
- C1.3 Plane label back-fill methodology — re-verify Block 4.B's
44/47 prefix→label mapping fresh, produce the issue-count-per-prefix
table, and recommend API-via-framework/plane_connector.py
(preserves audit trail, slow but tolerable) over direct DB write.
Surface the 3 unmatched prefixes for explicit user decision
(skip-and-surface vs auto-create labels).

🛑 GATE C1 (USER APPROVAL): I post the audit and explicitly
surface the three C1.2 decisions, the C1.3 implementation choice,
the 3 unmatched prefix tokens, and any architectural concerns from
the migration analysis. Wait for user approval before C2.

Phase C2 — NetBox deployment (canonical pattern)

- C2.1 Vault setup. Provisioning script
(scripts/provision-netbox.sh, idempotent, modeled on
scripts/provision-control-plane.sh):
  - secret/netbox/admin — 32-char generated random password;
Argon2 hash captured for verification, value never displayed.
  - secret/netbox/postgres — DB user/password.
  - secret/netbox/secret_key — Django SECRET_KEY (50+ char random).
  - secret/netbox/api_token — empty placeholder; populated
post-deployment in C2.7.
  - secret/netbox/email — deferred per default (no SMTP),
confirmable.
  - config/vault-policies/netbox-policy.hcl (modeled on
control-plane-policy.hcl).
  - AppRole netbox materials at ~/.vault-approle/netbox/ on Mac
Mini.
  - All token ops use -orphan.
  - Hash-only verification of every secret write.
- C2.2 Compose stack at docker/netbox/:
  - docker-compose.yml: netbox, netbox-worker, netbox-housekeeping,
netbox-postgres, netbox-redis, netbox-redis-cache,
vault-agent-netbox sidecar.
  - vault-agent/ directory with template renderer producing
/vault/secrets/netbox.env.
  - config/configuration.py template consuming rendered env via
env_file.
  - .env.template — placeholders only; no values; pre-commit
detect-secrets must pass.
  - README.md — operator guide with hash-only verification
examples.
  - Hardening: cap_drop: [ALL] everywhere; cap_add only on netbox
(CHOWN, SETUID, SETGID, FOWNER, DAC_OVERRIDE for Django static
collection); no-new-privileges: true everywhere; mem_limit (netbox
2g, postgres 1g, redis 512m, redis-cache 512m, worker 1g,
housekeeping 256m) calibrated per CLAUDE.md anti-undersize note;
tmpfs for /vault/secrets; entrypoint wrappers use exec.
- C2.3 Registry entry: append netbox (and its sidecars/datastore
entries — modeled on Plane's pattern of separate docker-plane-*
entries) to config/service-registry.yaml. Vault paths,
dependencies, health_check, tags [cmdb, infrastructure-as-data].
Yamllint must pass.
- C2.4 Caddy route: append netbox.internal block to
docker/caddy/Caddyfile using the canonical pattern (import
access_log, reverse_proxy host.docker.internal:8080, tls internal).
Reload via Caddy admin API; verify route returns 302→/login/ on
first hit.
- C2.5 Bring up the stack on Mac Mini: ssh admin@192.168.10.145
"cd ~/path/to/repo/docker/netbox && docker compose up -d". Watch
logs until NetBox listens on :8080 and migrations are applied.
- C2.6 First-time admin via manage.py createsuperuser --noinput;
password set via shell command using Vault-fetched value piped
through stdin (never argv, never echo); hash-only verification
(sha256 of fetched value compared to known-write hash from C2.1).
- C2.7 Generate API token via manage.py shell script that prints
token to stdout once, captured and immediately written to
secret/netbox/api_token. Verify via hash-of-fetched-from-vault
matches hash-of-captured. Token never displayed.
- C2.8 Verification:
  - All 7 NetBox-stack containers up.
  - vault-agent-netbox exit 0 after rendering (or healthy if
long-running).
  - /api/status/ returns 200 JSON.
  - API-token authentication round-trip succeeds.
  - netbox.internal serves login page through Caddy.
  - Vault audit log size delta confirms AppRole/KV reads.

Commit and push at the end of C2 per Commit-and-Push Doctrine.
Out-of-repo compose changes are limited to the Mac Mini bringing
the stack up; the compose files themselves live in the repo so no
~/control-center-stack/stacks/* rewire-log needed.

🛑 GATE C2: NetBox operational. If anything is unhealthy I stop
and surface — do not proceed to C3.

Phase C3 — Data migration (registry → NetBox)

- C3.1 Define NetBox custom fields via API/script. Custom fields
candidates from C1.1 audit (subject to C1 review): vault_paths
(longtext), health_check_endpoint (text), caddy_route (text),
platform_tags (multi-select), docker_compose_file (text),
service_dependencies (longtext or relationships if modeled as
devices). Created via pynetbox in a venv at
/Users/admin/.venv-block-4c/ (created on Mac Mini).
- C3.2 scripts/migrate-registry-to-netbox.py:
  - Read config/service-registry.yaml.
  - For each entry create/update a NetBox object — concrete shape
(Service vs Device vs VirtualMachine) decided by audit
recommendation in C1.1, surfaced in C1's gate.
  - Idempotent (uses ID/name lookup before create).
  - --dry-run mode prints planned creates/updates/skips without
touching NetBox.
  - Reads token from Vault via the netbox AppRole (no token in env
or argv).
- C3.3 Run --dry-run, surface output to user for review. 🛑 GATE
C3 (USER APPROVAL): wait for approval before live migration.
- C3.4 Run live migration. Side-by-side validation report
comparing each registry entry to the NetBox-loaded view; mismatches
surfaced.

Commit and push the migration script and validation artifact
(docs/phase-13/PHASE_13_BLOCK_4C_C3_MIGRATION_2026-04-29.md) at
end of C3.

Phase C4 — Plane label back-fill

- C4.1 Default implementation per C1.3 recommendation:
framework/plane_connector.py-based, with built-in 429 backoff.
(Direct DB option only if user explicitly chose it at C1.) Block
4.B addendum confirmed issues/-rooted endpoints have a
longer-window throttle on top of 60/min — script must respect that
with conservative pacing (initial guess: 1 req/sec with
exponential backoff to 1/min on 429).
- C4.2 scripts/backfill-plane-labels.py:
  - Enumerate all 604 issues via cursor pagination.
  - For each issue: extract RM-* prefix, look up matching label,
apply via API.
  - Idempotent: skip already-labeled issues with the same label.
  - Progress log every 100 issues.
  - 3 unmatched prefixes: behavior controlled by
--unmatched={skip|create}; default skip, surface a list at end.
(User chooses behavior at C1 gate.)
  - Plane API token sourced from Vault. Pre-flight memory hygiene:
the Block 4.B finding noted plaintext token at
~/.claude/projects/.../memory/plane_deployment.md. I will read
that token to confirm it matches Vault, redact the memory file
(replace value with reference to Vault path), and use the Vault
copy in the script. If the values diverge or the user prefers to
rotate first, I stop and surface.
- C4.3 --dry-run first, surface counts per prefix. 🛑 GATE C4
(USER APPROVAL): wait for approval. Then run live; report
progress.
- C4.4 Validation via Plane API: count of labeled issues > 0;
per-label distribution table; the 3 unmatched issues' disposition
documented.

Commit and push at end of C4.

Phase C5 — Deprecation of homegrown registry (USER APPROVAL gate)

- C5.1 Consumer scan — already previewed; the three primary
consumers are:
  a. docker/topology-api/server.py (mounts and re-reads YAML each
request).
  b. scripts/validate-cmdb.sh.
  c. docker/control-plane/app/modules/registry.py (Block 2.5's
control-plane mounts the YAML at /app/service-registry.yaml;
surfaced in pre-plan recon — this consumer is not in the prompt's
named list, so I'm flagging it explicitly here).

Plus documentation references in docs/PLATFORM_OVERVIEW.md,
docs/runbooks/add-new-service.md,
docs/runbooks/what-changed-last-24h.md, and
docs/architecture/dependency-graph.md — these are documentation,
not code, but require update.
- C5.2 Migrate each code consumer to the NetBox API. One commit
per consumer. Each migration runs side-by-side equivalence
(NetBox-backed output must match YAML-backed output for the same
query).

- Risk note: the control-plane container reads the registry as
part of its core operator-visualization flow. Migrating it touches
a Block-2.5-just-shipped service. I will:
  - First add a NetBox client module alongside the existing YAML
reader (additive).
  - Switch the call site behind a config toggle.
  - Verify equivalence on Mac Mini.
  - Default the toggle to NetBox, retain YAML fallback for one
block, then remove fallback at C5.4.

This staged approach is more conservative than the prompt's
implicit "swap and go" but preserves the Block 2.5 service's
stability. I'll surface this at C5.3 for user approval.
- C5.3 🛑 GATE C5 (EXPLICIT USER APPROVAL — the marquee gate of
4.C): present consumer migration outcomes, equivalence-validation
evidence, the staged-toggle approach for control-plane, and the
proposed deprecation step (config/service-registry.yaml →
config/service-registry.yaml.DEPRECATED with header pointing at
NetBox + git history retained). Wait for explicit "approved,
deprecate".
- C5.4 Execute on approval: rename, add deprecation header, update
CLAUDE.md to name NetBox as the source of truth (and retire the
"Post-Block-2 Follow-up List" item that references the registry).
Commit and push.

Phase C6 — Final regression + closeout

- C6.1 Run bash docs/phase-13/h1-regression-probe.sh block-4c-final
on Mac Mini. Require PASS=15 FAIL=0 zero new WARN. The probe
currently has an item validating validate-cmdb.sh-style drift; if
the probe needs updates because we migrated validate-cmdb.sh to
NetBox in C5, that update happens inside C5.2 as part of consumer
migration, not as an opportunistic edit at C6.
- C6.2 Closeout:
docs/phase-13/PHASE_13_BLOCK_4C_CLOSEOUT_2026-04-29.md with each
phase summary, hash-only verification table for new Vault paths,
NetBox object/custom-field/relationship counts, Plane
label-distribution table, consumer migration outcomes, regression
results, follow-ups (e.g., InvenTree wiring point in 4.D,
cross-index in 4.E, the pending memory-file token redaction
confirmed). Commit and push.
- C6.3 Doctrine update: CLAUDE.md "Current Phase" line and a new
bullet under "Heterogeneous Architecture" or a new "CMDB"
sub-section noting NetBox is the agent-queryable source for "what
services exist".

Tag at C6 close: none (per spec — the only tag in this block is
implicit in main's commit history; the gating tag was
v13-block-3-close at Block 4.A close).

---

Risk register and mitigations

Risk: NetBox migration introduces a breaking import — initial
manage.py migrate has known pitfalls on M-series Mac via Docker
Desktop
Mitigation: Use the pinned netbox-docker tag from upstream; if
migration fails, capture full logs and surface, do not auto-bypass
with --fake.
────────────────────────────────────────
Risk: pynetbox API client behaves differently per NetBox version
Mitigation: Pin pynetbox in venv requirements; verify against the
deployed NetBox /api/status/ version field.
────────────────────────────────────────
Risk: Plane API rate limit pushes back-fill past 1 hour estimate
Mitigation: Block 4.B addendum already confirmed issues/-rooted
bucket is throttled. Conservative 1 req/sec floor; if back-fill
estimated >4 hours, stop and surface to ask user about direct-DB
alternative.
────────────────────────────────────────
Risk: control-plane consumer migration breaks Block 2.5 deliverable
Mitigation: Staged toggle approach (C5.2 risk note); staged through
equivalence validation before flipping default.
────────────────────────────────────────
Risk: Plaintext Plane token in memory file (Block 4.B finding) —
leaks risk if memory committed/shared
Mitigation: C4.2 memory hygiene step: read once, compare with
Vault, redact memory, use Vault copy in scripts. Surface if
divergent.
────────────────────────────────────────
Risk: Custom-field schema in NetBox needs to evolve mid-migration
Mitigation: C3.1 uses idempotent script — deletes/recreates custom
fields safely under script control rather than ad-hoc UI clicks.
────────────────────────────────────────
Risk: Out-of-repo compose change leakage
Mitigation: All NetBox compose files live under docker/netbox/ in
the repo; no out-of-repo edits anticipated. If any arise (e.g., a
Caddy/Homepage stack-level change), pre/post snapshots written to a
rewire log.
────────────────────────────────────────
Risk: Pre-commit detect-secrets blocks a commit (e.g., flagging
.env.template entropy)
Mitigation: Don't --no-verify. Investigate, mark template values as
obvious-placeholders (__VAULT_RENDERED__) or update detect-secrets
baseline carefully with audit trail.

Estimated effort

8–12 hours focused execution per the prompt's estimate, distributed
roughly:
- C0/C1: 1–2 h (audit doc + recon)
- C2: 3–4 h (Vault setup + canonical-pattern compose + first-boot)
- C3: 1–2 h (custom fields + migration script + validation)
- C4: 1–2 h (script + dry-run + back-fill, gated by Plane rate
limit)
- C5: 2–3 h (consumer migration is the largest unknown; staged
toggle for control-plane adds time)
- C6: 30–45 min (regression + closeout)

What I will surface at each gate

- C1 gate: the 3 NetBox topology decisions, Plane label back-fill
choice (API vs DB), the 3 unmatched prefix tokens, audit doc
itself.
- C2 gate: any unexpected behavior; default is auto-proceed to C3
on green.
- C3 gate: dry-run output (planned creates/updates/skips per
service).
- C4 gate: dry-run output (issue count per prefix; the 3
unmatched).
- C5 gate (the marquee): consumer migration evidence + equivalence
proofs + staged-toggle approach for control-plane + deprecation
diff preview.
