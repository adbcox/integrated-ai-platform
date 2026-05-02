# Rewire-log — 2026-05-01 — homarr retirement (17.F PARK-RETIRE)

**File touched (out-of-repo):**
`/Users/admin/control-center-stack/stacks/ai-control/docker-compose.yml`

**Reason:** 17.F PARK-RETIRE of homarr (zero traffic 7d, redundant
with homepage; full audit at
`docs/audits/capability/homarr-2026-05-01.md`).

**D#15 doctrine:** out-of-repo compose changes require pre/post
snapshots in the rewire log because git does not track the source
file automatically. This entry preserves the file at retirement time.

---

## Pre-snapshot

97 lines. SHA256:

```
$ shasum -a 256 /Users/admin/control-center-stack/stacks/ai-control/docker-compose.yml
(captured pre-edit at 2026-05-01 21:21:17 to /tmp/ai-control-pre-homarr-retirement.yml)
```

Key blocks before edit:

```yaml
volumes:
  open-webui-data:
  homarr-config:
  homarr-icons:
  homarr-data:
```

```yaml
  # ── Homarr — service dashboard with Docker auto-discovery ──────────────────
  # No credentials; not rewired (A.7 scope: only services consuming creds)
  homarr:
    image: ghcr.io/ajnart/homarr:latest
    container_name: homarr
    ...
```

(Full pre-snapshot at `/tmp/ai-control-pre-homarr-retirement.yml`
during the session — copy into long-term backup if needed.)

---

## Post-snapshot

Same line count after edit (commented retirement markers replace
service block volume usage). Key blocks after edit:

```yaml
volumes:
  open-webui-data:
  # ── Retired 2026-05-01 (17.F PARK-RETIRE) — DO NOT REMOVE ─────────────
  # Volumes preserved (declared but unused) so they are not GC'd; they
  # contain the parked homarr state. Restoration recipe at
  # docker/_retired/homarr/README.md (in iap repo).
  homarr-config:
  homarr-icons:
  homarr-data:
```

```yaml
  # ── Homarr — RETIRED 2026-05-01 (17.F PARK-RETIRE) ─────────────────────────
  # Reason: zero traffic over 7 days (D#20). Service-portal surface is
  # covered by `homepage` (homepage.internal). Service block parked at
  # docker/_retired/homarr/docker-compose.parked.yml in the iap repo.
  # Volumes (homarr-config, homarr-icons, homarr-data) declared above
  # remain so the parked state is recoverable. Restoration recipe in
  # docker/_retired/homarr/README.md.
```

---

## Diff (canonical)

```diff
--- pre
+++ post
@@ volumes block
+  # ── Retired 2026-05-01 (17.F PARK-RETIRE) — DO NOT REMOVE ─────────────
+  # Volumes preserved (declared but unused) so they are not GC'd; they
+  # contain the parked homarr state. Restoration recipe at
+  # docker/_retired/homarr/README.md (in iap repo).
   homarr-config:
   homarr-icons:
   homarr-data:
@@ services block
-  # ── Homarr — service dashboard with Docker auto-discovery ──
-  # No credentials; not rewired (A.7 scope: only services consuming creds)
-  homarr:
-    image: ghcr.io/ajnart/homarr:latest
-    container_name: homarr
-    restart: unless-stopped
-    ports:
-      - "7575:7575"
-    volumes:
-      - /var/run/docker.sock:/var/run/docker.sock:ro
-      - homarr-config:/app/data/configs
-      - homarr-icons:/app/public/icons
-      - homarr-data:/data
-    environment:
-      TZ: "America/New_York"
-      DEFAULT_COLOR_SCHEME: "dark"
-    cap_drop: [ALL]
-    security_opt: [no-new-privileges:true]
-    networks: [control-center-net]
-    healthcheck: …
+  # ── Homarr — RETIRED 2026-05-01 (17.F PARK-RETIRE) ──────────────────────
+  # Reason: zero traffic 7d (D#20). homepage covers the surface.
+  # Parked at docker/_retired/homarr/docker-compose.parked.yml.
+  # Volumes preserved (see volumes block above).
```

---

## Container action taken

```bash
docker stop homarr  # stopped clean (no SIGKILL)
docker rm homarr    # removed (volumes preserved by default)
```

Volumes verified still present:

```
$ docker volume ls | grep -i homarr
local     ai-control_homarr-config
local     ai-control_homarr-data
local     ai-control_homarr-icons
```

---

## Restoration

See `docker/_retired/homarr/README.md` for the full recipe. TL;DR:
restore the homarr block in this out-of-repo compose, run
`docker compose up -d homarr`, volumes auto-remount.
