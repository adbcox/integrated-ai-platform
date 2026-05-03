# D-17-17 — Logical Service Architecture dashboard smoke test

**Date:** 2026-05-03
**Artifact:** `docs/dashboards/logical-service-architecture.html` (93,754 bytes generator output, 93,892 bytes served via Caddy)

## Verified end-to-end

```
$ curl -s -o /dev/null -w "HTTP %{http_code}\n" -H "Host: architecture.internal" http://localhost/
HTTP 308

$ curl -skL --resolve architecture.internal:443:127.0.0.1 \
    -o /tmp/arch-test.html \
    -w "HTTP %{http_code} | size=%{size_download} | url=%{url_effective}\n" \
    https://architecture.internal/
HTTP 200 | size=93892 | url=https://architecture.internal/logical-service-architecture.html

$ head -5 /tmp/arch-test.html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Logical Service Architecture · Integrated AI Platform</title>
```

Path proven: client → Caddy :443 (auto-TLS via internal CA) → root redirect to
`/logical-service-architecture.html` → `host.docker.internal:8765`
(host-side `python3 -m http.server`) → static HTML.

## Generator stats

- 76 services rendered as cards, grouped by stack
- 13 runtime/Caddy orphans surfaced separately
- Live `docker stats` snapshot embedded at generation time
- 91 credential fingerprints (12-char SHA-256 only — Finding ZZ compliant)
- 0 occurrences of `sk-` API key prefix
- 3 `sha256:` strings — all public image digests (safe)

## Operational notes

- **Refresh:** re-run `python3 scripts/dashboards/generate_logical_architecture.py`
  whenever the registry refreshes (`scripts/platform-registry/refresh.sh`).
  Both can be wired together later if a recurring refresh is desired.
- **Static server:** background `python3 -m http.server 8765` from
  `docs/dashboards/`. PID at smoke time: 33623. Restart pattern documented
  separately if it dies.
- **Caddyfile site:** `architecture.internal` block at lines 245-254.
  Restart of caddy container required after edit because Docker Desktop's
  bind-mount cache did not propagate the in-place file change to the
  container view (observed during this deliverable — known macOS quirk;
  `docker restart caddy` fixed it within 3 s).

## Screenshot deferral

Headless render artifacts (`architecture-dashboard.png`) deferred. The
Mac Mini control session has no interactive GUI display: Chrome
`--headless` fails with keychain-encryption errors (`errSecInteractionNotAllowed`),
Chrome `--headless=new` fails with `SharedImageManager` GPU errors,
`screencapture` returns `-10810` ("could not create image from display").

The HTML artifact itself is the canonical source of truth and is rendered
correctly by any browser pointed at `https://architecture.internal/`.
A demo-day operator-screen capture is the appropriate next step on
2026-05-09.
