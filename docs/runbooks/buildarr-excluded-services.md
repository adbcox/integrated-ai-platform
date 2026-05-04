# Buildarr-excluded services — reactive management workflow

**Status:** Active. Audited 2026-05-04 (D-17-77).
**Doctrine:** `docs/architecture-facts/integration-audit-doctrine.md` Finding 11.
**CLAUDE.md block:** "Buildarr Config-as-Code Doctrine (D-17-44)".

Buildarr is the canonical config authority for Radarr (full coverage) and
Prowlarr applications. **Some arr-stack surfaces fall outside Buildarr's
coverage** — the upstream plugin doesn't support them, doesn't exist, or
exposes a schema gap. Those surfaces are **reactive-managed**: configuration
changes happen in the live UI/API; Buildarr will not capture, replay, or
revert them.

This runbook lists what is excluded, what that means in practice, and the
operator-facing workflow for changing each excluded surface without
introducing silent drift.

## Excluded surfaces (audit 2026-05-04)

| Surface | Reason for exclusion | Reactivation path |
|---|---|---|
| **Sonarr v4** (running v4.0.17.2952) | `buildarr-sonarr 0.6.4` plugin supports Sonarr v3 only. Latest PyPI description: *"Currently, Sonarr V3 is the only supported version. Sonarr V4 support is planned for the future."* | Wait for upstream v4 plugin. When it lands, run `buildarr sonarr dump-config` against live Sonarr, append the rendered YAML into `config/arr-stack/buildarr/buildarr.yml`, commit, run `buildarr-run.sh` to confirm idempotent. |
| **Sportarr** | No Buildarr plugin exists (`pypi.org/pypi/buildarr-sportarr/json` → 404). Neither official nor community packages found. | If a community plugin lands, treat as Sonarr v4 reactivation pattern. Until then, Sportarr restoration playbook is the retirement record at `docs/_retired/sportarr-2026-05-01.md` patched per D-17-36. |
| **Prowlarr indexer definitions** | `buildarr-prowlarr` schema gap — `dump-config` returns indexer count = 0. Plugin doesn't model indexer rows. | Wait for upstream plugin extension. `delete_unmanaged: false` in `buildarr.yml` already protects existing indexer definitions from being deleted. |
| **Prowlarr download clients** | Same plugin schema gap as indexer definitions. | Same as above. |

## What "reactive-managed" means for these surfaces

For surfaces **inside** Buildarr coverage:
- The committed YAML is the source of truth.
- Manual UI changes are reverted on the next daily run.
- Drift between live state and YAML is detected by `buildarr <plugin> dump-config` diff.

For excluded surfaces:
- The **live service config is the source of truth** (its own DB, its own `config.xml`).
- Manual UI changes persist; nothing reverts them.
- There is no built-in drift detection. A change you make today and forget about will still be there next year — and there's no commit record of why.

The implication: **every change to an excluded surface should leave a paper trail somewhere outside the live service**. Options below.

## Operator workflow — changing an excluded surface

### Step 1 — decide if the change is config-class or operational-class

- **Config-class** (quality profile, custom format, indexer setup, application URL, notification target): the kind of change Buildarr would have managed. Needs a paper trail.
- **Operational-class** (manually triggered search, retag, library refresh): no paper trail needed; ephemeral.

Only config-class changes are in scope for this runbook. If you can't decide which class applies: assume config-class.

### Step 2 — make the change in the live UI

Standard Sonarr/Sportarr/Prowlarr UI operation. No special posture.

### Step 3 — record the change

Pick one. Order is from lightest to heaviest record:

**3a — commit message footnote.** If you're already touching the repo for a related reason (a runbook update, a doctrine note, a sibling deliverable), append a one-line annotation to that commit's body:

```
Sidebar: changed Sonarr v4 quality profile "WEB-1080p" cutoff from
HDTV-1080p to WEBRip-1080p; reactive-managed (D-17-77 runbook), will
re-capture into buildarr.yml when buildarr-sonarr v4 lands.
```

This is the lightest record and preferred for small changes that fit into ongoing work.

**3b — note in the relevant deliverable's closeout.** If the change is part of a deliverable's scope, document it in that deliverable's chronicle alongside the structural changes.

**3c — discrete `docs/_arr-changes/<date>-<service>-<short-name>.md` note.** For changes that don't have an obvious commit or deliverable to attach to. Format:

```markdown
# <date> — <service> reactive change: <short-name>

## What changed
<plain English description>

## Why
<reason — usually a quality, performance, or compatibility concern>

## How to verify
<one-line probe: a curl command, a UI navigation path, a DB query>

## Restoration playbook (if Sonarr v4 / Sportarr config is lost)
<minimal steps to re-apply this change manually>
```

The `_arr-changes/` directory is a phase-agnostic accumulator, not a deliverable. Files there are read on demand during restoration audits. Do **not** create the directory unless you have something to put in it.

### Step 4 — for Sonarr v4 specifically: snapshot config.xml

If the change touched Sonarr v4 settings that round-trip through `/config/config.xml` (URL base, port, branch, log level, auth):

```bash
docker exec sonarr cat /config/config.xml > /tmp/sonarr-config-$(date +%Y%m%d).xml
diff /tmp/sonarr-config-$(date +%Y%m%d).xml \
     /tmp/sonarr-config-<previous>.xml
```

Commit the diff (not the file) into the change-note from Step 3c. The `config.xml` itself contains the Sonarr API key and **must not be committed**; only its diff with the API key line redacted.

## Drift recovery — "I think someone changed something but I don't have a record"

For Sonarr v4: `docker exec sonarr cat /config/config.xml` shows the live config. Diff against your earliest known snapshot. For DB-backed settings (quality profiles, custom formats, indexer config), there's no built-in dump tool — open the UI section and compare visually against your memory. If memory is unreliable: re-derive the desired state from first principles, set it, and capture per Step 3.

For Sportarr: same as Sonarr v4, plus the D-17-36 chronicle (`integration-audit-doctrine.md` Finding 6) catalogs the most failure-prone Sportarr settings (indexer URL column name, ApiKey staleness, bind-mount canonical pattern, storage layout) — start there.

For Prowlarr indexer definitions: `Indexers` table in `prowlarr.db`. Definitive listing via:

```bash
docker exec prowlarr sqlite3 /config/prowlarr.db \
  "SELECT Id, Name, Implementation, BaseUrl FROM Indexers;"
```

For Prowlarr download clients: `DownloadClients` table in `prowlarr.db`. Same query pattern.

## What this runbook does NOT cover

- **Credentials**. Vault is the authority for secrets regardless of Buildarr coverage. API key rotation, Vault re-writes, and AppRole provisioning are unchanged for excluded services. See `docs/runbooks/rotate-credentials.md`.
- **Health checks**. Selfheal (D-17-38) probes excluded services the same way as Buildarr-managed ones; integration health is orthogonal to config authority.
- **Container lifecycle**. `docker compose up -d <service>` works the same for excluded and managed services. Buildarr exclusion is a config-plane property, not a runtime property.

## When to retire this runbook

When **all three** are true:

1. `buildarr-sonarr` plugin supports Sonarr v4 (PyPI description no longer says "v3 only").
2. `buildarr-sportarr` plugin exists on PyPI (community or official).
3. `buildarr-prowlarr` schema gaps for indexer definitions + download clients have closed (`dump-config` returns non-empty rows for both).

At that point, run a fresh `dump-config` against each, fold into `buildarr.yml`, commit, and replace this runbook with a brief note in `_archive/` pointing at the F11 chronicle.

## Cross-references

- `docs/architecture-facts/integration-audit-doctrine.md` Finding 11 — declarative-config-as-code doctrine + first worked example
- `CLAUDE.md` "Buildarr Config-as-Code Doctrine (D-17-44)" — operator-facing scope statement
- `config/arr-stack/buildarr/buildarr.yml` — committed canonical config for managed surfaces
- `scripts/buildarr-run.sh` — daily reconciliation runner (launchd `com.iap.buildarr-sync` at 03:00)
- `docs/_retired/sportarr-2026-05-01.md` (patched per D-17-36) — Sportarr restoration playbook for the no-plugin path
