# Retired — homarr

**Retired:** 2026-05-01 (Phase 17 deliverable 17.F PARK-RETIRE)
**Audit:** [docs/_audit/capability/homarr-2026-05-01.md](../../../docs/_audit/capability/homarr-2026-05-01.md)
**Pattern:** PARK-RETIRE (compose parked, volumes preserved)
**D#15 rewire-log:** [docker/_rewire-log/2026-05-01-homarr-retirement.md](../../_rewire-log/2026-05-01-homarr-retirement.md)

---

## Why retired

D#20 probe on 2026-05-01:
- ~110 kB rx / 3.4 kB tx over 7-day window — essentially zero traffic.
- Operator's primary portal is `homepage.internal` (homepage container).
- `homarr.internal` had no Caddy front (no operator-facing route).

Surface coverage is preserved by `homepage` alone — no operator-facing
gap.

~176 MiB RAM recovered.

---

## Original compose location

**Out-of-repo:** `~/control-center-stack/stacks/ai-control/docker-compose.yml`

This is significant under D#15 (out-of-repo compose changes require
rewire-log entries because git doesn't track the source).

The live compose now contains a retirement marker comment in place of
the homarr service block, plus the three named-volume declarations
(uncommented but with a `# DO NOT REMOVE` marker).

---

## Volumes preserved

```
ai-control_homarr-config
ai-control_homarr-icons
ai-control_homarr-data
```

Verify: `docker volume ls | grep -i homarr` (3 entries expected).

These survive retirement. Volumes are not GC'd because the
out-of-repo compose still declares them (see `volumes:` block in
the live compose).

---

## Restoration recipe

```bash
# 1. Restore the homarr service block in the out-of-repo compose
$EDITOR ~/control-center-stack/stacks/ai-control/docker-compose.yml
#    a) Replace the "RETIRED 2026-05-01" comment block with the
#       service block from docker-compose.parked.yml in this dir.
#    b) Optional: remove the "DO NOT REMOVE" comment from the
#       volumes block (no functional change).

# 2. Bring the container back
cd ~/control-center-stack/stacks/ai-control
docker compose up -d homarr

# 3. Volumes auto-remount (config + icons + data preserved)
docker ps | grep homarr
curl -sf http://localhost:7575/  # should return HTTP < 500
```

Update the rewire-log with a "restoration" note if reactivating.

---

## What lives in the volumes

- `ai-control_homarr-config` — homarr's YAML configs (board layouts,
  widgets, integrations).
- `ai-control_homarr-icons` — uploaded icons.
- `ai-control_homarr-data` — runtime data (sessions, etc.).

Restoration recovers everything that was in the running instance at
retirement time.
