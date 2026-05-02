# OpenProject sync from PROJECT_FRAMEWORK.md — Runbook

**Status:** Live (D-17-04 WP-17-04-04, 2026-05-02)
**Replaces:** `docs/runbooks/plane-sync.md` (retired with Plane CE in WP-17-04-06)
**Script:** `scripts/openproject-sync-from-framework.py`
**Source of truth:** `docs/PROJECT_FRAMEWORK.md` §7 (Phase 15) + §8 (Phase 16) + §9 (Phase 17)
**OpenProject project:** identifier `roadmap` at `http://192.168.10.145:8086`
**Token:** `secret/openproject/api#token` (Vault), iap-sync user, scoped via the
`IAP Sync` ProjectRole. Pulled by the script via the `vault-server` container.
**Doctrine:** ADR-A-006 — repo-owned docs are canonical; OpenProject is an
operational overlay. Sync is one-way (repo → OpenProject); UI edits to synced
fields are overwritten on the next run.

## 1. Purpose

Maintain an OpenProject mirror of the Phase / Deliverable table in
PROJECT_FRAMEWORK.md so operators viewing OpenProject see the same set of
deliverables, in the same states, as the canonical markdown. The sync is a
one-way write from repo to OpenProject.

The sync underpins D-16-06 (drift detection): `--dry-run` exits 2 when
changes are pending, which the CI hook uses to fail loudly when the markdown
table and the OpenProject state disagree.

ADR stubs (any WP whose External ID starts with `ADR-`) are **not** touched
by this sync — they are owned by `scripts/cross-index-validate.py`.

## 2. What it materialises

For every phase in PROJECT_FRAMEWORK.md:

- One **Version** named `Phase-NN` (Versions are OpenProject's analog to
  Plane Modules; OpenProject doesn't natively support external_id on
  Versions, so the canonical key is the name).
- One **WorkPackage** keyed by External ID `Phase-NN`, summarising the
  phase header.
- One **WorkPackage** per deliverable, keyed by External ID (e.g.
  `D-16-02`, `D-16-02.A`, `D-15-08`, `17.A`), associated with the
  phase Version via the `version` link.

Status mapping (markdown → OpenProject status name):

| Markdown    | OpenProject status |
|-------------|--------------------|
| DONE        | Closed             |
| IN PROGRESS | In progress        |
| NOT STARTED | New                |
| DEFERRED    | On hold            |

## 3. Modes

```bash
# Dry-run (plan only; exit 2 if changes pending, 0 if clean)
/Users/admin/.venv-block-4c/bin/python scripts/openproject-sync-from-framework.py --dry-run

# Apply
/Users/admin/.venv-block-4c/bin/python scripts/openproject-sync-from-framework.py

# Limit to a single phase
/Users/admin/.venv-block-4c/bin/python scripts/openproject-sync-from-framework.py --dry-run --phase 17
```

Exit codes:
- `0` — no changes pending (or apply succeeded)
- `2` — dry-run with pending changes (CI hook treats this as drift)
- `3` — OpenProject saturated (rate-limited; not normally hit)

## 4. Idempotency

- Versions matched by name (== external_id).
- WorkPackages matched by External ID custom field (id 2). Legacy "Plane
  RM ID" custom field (id 1) is preserved on the 670 WPs imported from
  Plane in WP-17-04-03 but is no longer written.
- Description diff compares **markdown raw**, not rendered HTML —
  OpenProject canonicalises stored markdown to `<p class="op-uc-p">` /
  `<code class="op-uc-code">` on read, so HTML-vs-HTML always diffs.

## 5. Prerequisites — first-time setup on a fresh OpenProject

If OpenProject was just deployed or the iap-sync user / role doesn't yet
exist, run these in order:

```bash
# 1. Mint the iap-sync user, role, membership, workflows, and rotate
#    its API token into Vault. Idempotent.
./scripts/openproject-mint-iap-sync-token.sh

# 2. Create the 'External ID' custom field, enable on all types, and
#    backfill from WP subjects (parses '[D-NN-XX]' / '[Phase-NN]' /
#    '[NN.X]' prefix). Idempotent.
./scripts/openproject-bootstrap-ext-id-field.sh
```

The mint script performs five subsystem-level setups in one shot:

1. ProjectRole `IAP Sync` with WP CRUD + version/category management
2. User `iap-sync` (low-priv, non-admin)
3. Membership on the `roadmap` project
4. Enables the `work_package_tracking` module on the project (without
   this, *every* WP API permission check returns false)
5. Workflow rows: clones Member's transitions and adds explicit
   `*→{New, In progress, Closed, On hold, Rejected}` for every type.
   The OpenProject API requires workflow rows for any sync operation
   AND for `/api/v3/statuses` to be reachable at all.

## 6. Vault paths touched

- `secret/openproject/api#token` (read) — iap-sync user's API token

## 7. Behaviour on UI drift

If an operator edits a synced WP's subject, status, or description in
the OpenProject UI, the next sync APPLY will overwrite those edits to
match PROJECT_FRAMEWORK.md. This is intentional. The OpenProject UI is
the right surface for comments, sub-tasks, and operational links — not
for redefining deliverable scope.

To change a deliverable's title or status: edit the markdown table.

## 8. Troubleshooting

**`HTTP 403 MissingPermission` on form/statuses endpoints**
The iap-sync role has zero workflow rows. Re-run
`./scripts/openproject-mint-iap-sync-token.sh` — it clones Member's
workflows and adds explicit transitions.

**`HTTP 422 Status is invalid because no valid transition exists`**
Same root cause: missing workflow row for the from→to combination.
Re-running the mint script adds explicit `*→{sync target}` transitions
for every type.

**Description always flags as drift**
The diff is comparing on `description.html` instead of `description.raw`.
Check that the connector's `_materialize_wp` returns `description_raw`
and the sync's `_diff_issue` uses `_html_to_markdown(want_desc)` for
the comparison.

**Sync wants to create WPs that already exist**
The 670 imported WPs have External ID empty until
`openproject-bootstrap-ext-id-field.sh` is run. Verify CF id 2 has
`is_for_all=true` and that the project lists "External ID" as an
enabled WP custom field. The bootstrap script is idempotent.

## 9. Related

- `docs/runbooks/drift-detection.md` — uses the dry-run exit code
- `docker/openproject/README.md` — OpenProject deployment + Vault paths
- `framework/openproject_connector.py` — REST client (Plane-compat shape)
- `scripts/openproject-mint-iap-sync-token.sh` — bootstrap user/role/token
- `scripts/openproject-bootstrap-ext-id-field.sh` — bootstrap the External ID CF
