# Indexer Strategy Doctrine

Date: 2026-05-04
Deliverable: D-17-106

## Current indexer inventory (post D-17-106)

| Indexer | Privacy | Protocol | TV | Movies | Music | Sports | FlareSolverr |
|---|---|---|---|---|---|---|---|
| 1337x | public | torrent | ✓ | ✓ | ✓ | — | required (tag: flaresolverr) |
| EZTV | public | torrent | ✓ | — | — | — | required |
| showRSS | public | torrent | ✓ | — | — | — | no |
| Knaben | public | torrent | ✓ | ✓ | ✓ | ✓ | no |
| YTS | public | torrent | — | ✓ | — | — | no |
| LimeTorrents | public | torrent | ✓ | — | ✓ | — | no |
| BT.etree | public | torrent | — | — | ✓ | — | no |
| TorrentDay | private | torrent | ✓ | ✓ | ✓ | — | no |
| NZBgeek | private | usenet | ✓ | ✓ | ✓ | — | no |

**Note:** LimeTorrents exposes `2000` (Movies) in its category map but Radarr v6
rejects it on sync because no movie sub-categories (2010/2020/etc.) are present in
the LimeTorrents Torznab caps. LimeTorrents syncs to Sonarr, Lidarr, Sportarr.

## Per-app indexer coverage (post D-17-106)

| App | Indexer count | Public torrent | Private torrent | Usenet |
|---|---|---|---|---|
| Sonarr | 6 | 1337x, showRSS, Knaben, LimeTorrents | TorrentDay | NZBgeek |
| Radarr | 4 | Knaben, YTS | TorrentDay | NZBgeek |
| Lidarr | 4 | Knaben, LimeTorrents, BT.etree | TorrentDay | NZBgeek |
| Sportarr | 7 | 1337x, EZTV, showRSS, Knaben, LimeTorrents | TorrentDay | NZBgeek |

## FlareSolverr-required indexers

1337x and EZTV require FlareSolverr to bypass Cloudflare challenge pages. They are
tagged `flaresolverr` (Prowlarr tag id=1) and the proxy is configured to
`http://flaresolverr:8191/` (Mac Mini Docker container on control-center-net).

**Prowlarr's internal backoff mechanism:** when a FlareSolverr-dependent indexer fails
(e.g., because FlareSolverr was temporarily misconfigured or network-isolated), Prowlarr
records a `disabledTill` timestamp for up to 24h. During that window, Prowlarr skips the
indexer even if the underlying issue is fixed. No manual intervention is required — the
backoff expires on its own schedule. Do NOT force-enable an indexer in this state without
understanding why it failed; if FlareSolverr is verified working (probe-before-assume),
the backoff expiry is the correct resolution path.

## Public-vs-private decision tree

```
New indexer needed?
├── Has Prowlarr schema entry? (GET /api/v1/indexer/schema | jq '[.[].name]')
│   ├── NO → out of scope; file separate deliverable for custom definition
│   └── YES →
│       ├── Public? → add directly (no credentials required)
│       └── Private? → requires operator credentials/invite
│           ├── Operator has account? → add with credentials via Vault
│           └── No account? → document in backlog, do NOT auto-signup
└── No schema entry + Prowlarr-supported custom YAML? → separate deliverable (not D-17-106 scope)
```

## Sports indexer gap

No Prowlarr-supported public indexer has a standard Newznab sports category (5060).
Private trackers with sports categories (BitHDTV, IPTorrents, SpeedCD, XSpeeds) require
invites. Knaben has a custom sports category (2106000) and is the best available public
option — it syncs to Sportarr via the general TV category (5000) sync path.

If sports-specific coverage is needed: file a separate deliverable for IPTorrents or
similar private tracker integration when operator obtains credentials.

## Known private trackers worth adding (requires credentials/invite)

| Indexer | Strength | Registration |
|---|---|---|
| Redacted | Music — highest quality, best metadata | Invite-only |
| Orpheus | Music — Redacted fork, similar quality | Invite-only |
| MyAnonamouse | Music + audiobooks, large catalog | Interview-based (open) |
| DimeADozen | Live recordings, concerts | Open |
| IPTorrents | General + Sports | Invite-only |

When operator obtains any of these: create a new D-17-NN deliverable, store credentials
in Vault (`secret/prowlarr/indexers/<name>`), add via Prowlarr API with credential fields.

## Indexer health check procedure (Finding 20/22 doctrine)

When a Prowlarr indexer shows unhealthy:

1. Check `GET /api/v1/indexerstatus` — is there a `disabledTill` timestamp?
   - YES and `disabledTill` is in the future → Prowlarr backoff; wait for expiry
   - YES and `disabledTill` is past → Prowlarr should re-enable on next attempt

2. Probe from Mac Mini host (not Docker):
   `curl http://<indexer-host>/probe-path` — does it return expected response?

3. If step 2 succeeds, probe from inside Prowlarr container:
   `docker exec prowlarr curl -sf http://<indexer-host>/probe-path`
   - If step 3 fails: network isolation issue (Finding 22 pattern — QNAP, external block, etc.)
   - If step 3 succeeds: Prowlarr config or auth issue

4. For FlareSolverr-dependent indexers: test FlareSolverr solve from inside container:
   `docker exec prowlarr curl -X POST http://flaresolverr:8191/v1 -d '{"cmd":"request.get","url":"<indexer-url>"}'`
   - status=ok, solution_status=200 → FlareSolverr working; issue is elsewhere
   - status=error → FlareSolverr config or target site issue

Never assume an indexer is broken based solely on Prowlarr health UI.
Always complete steps 2–4 before taking corrective action.

## Adding a new indexer (operational procedure)

```sh
PROWLARR_KEY="$(docker exec prowlarr sh -lc "sed -n 's:.*<ApiKey>\(.*\)</ApiKey>.*:\1:p' /config/config.xml | head -n1")"

# 1. Find schema entry
curl -sf -H "X-Api-Key: ${PROWLARR_KEY}" http://192.168.10.145:9696/api/v1/indexer/schema | \
  jq '[.[] | select(.name == "<IndexerName>")]'

# 2. Idempotency check
curl -sf -H "X-Api-Key: ${PROWLARR_KEY}" http://192.168.10.145:9696/api/v1/indexer | \
  jq '[.[].name]'

# 3. POST (public indexer — no credentials)
curl -sf -X POST \
  -H "X-Api-Key: ${PROWLARR_KEY}" \
  -H "Content-Type: application/json" \
  http://192.168.10.145:9696/api/v1/indexer \
  -d '<schema-payload + {appProfileId:1, priority:25, enable:true, tags:[]}>'

# 4. Trigger sync
curl -sf -X POST \
  -H "X-Api-Key: ${PROWLARR_KEY}" \
  -H "Content-Type: application/json" \
  http://192.168.10.145:9696/api/v1/command \
  -d '{"name":"ApplicationIndexerSync"}'

# 5. Verify from inside container
docker exec prowlarr curl -sf --max-time 20 \
  "http://localhost:9696/api/v1/search?query=<test-query>&indexerIds=<id>&type=search&limit=3" \
  -H "X-Api-Key: ${PROWLARR_KEY}" | jq 'length'
```
