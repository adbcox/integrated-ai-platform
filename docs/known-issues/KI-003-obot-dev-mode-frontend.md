---
ki: KI-003
title: obot's UI returns 502 on /
severity: LOW
status: RESOLVED
disposition: closed-as-resolved-per-audit-Q6
discovered: 2026-04-27
phase: pre-Phase-17 (Phase 7-era obot deployment; frontmatter migration 2026-05-11 per phase-17-closeout-audit Brief B Q6)
---

# KI-003: obot's UI returns 502 on /

## Status
RESOLVED — root cause was `OBOT_DEV_MODE: "true"` in obot-stack.yml. Setting it to `"false"` makes obot serve the API on `/api/` (returns 403 = auth required, valid) and return clean 404 on UI paths. The obot:latest image does not bundle a built UI (it's API-only); 404 on `/` is the correct response. obot.internal validates verify=0 http=404 (in the 2xx-4xx pass range).

## Observation
`https://obot.internal/` returns 502 Bad Gateway. obot logs show:
```
http: proxy error: dial tcp [::1]:5174: connect: connection refused
```

## Cause
obot is configured in dev mode where the SPA frontend is expected to be served
by a Vite dev server on port 5174 inside the container. Vite is not running, so
the proxy fails on root paths.

## Verification that backend works
- `/api/` returns 403 (auth required — correct response)
- `/oauth2/login` returns 302 (redirect — correct)

## Fix path
Reconfigure obot to use the production-built static frontend bundle, or run
the Vite process in the container. This is an obot configuration concern
unrelated to Phase 7 routing.

## Created
Mon Apr 27 21:50:03 EDT 2026

## Disposition (2026-05-11)

Disposition recorded per phase-17-closeout-audit §6 Q6: closed-as-resolved given evidence chain (root cause identified — `OBOT_DEV_MODE: "true"`; fix applied — flipped to `"false"`; verification confirmed — `obot.internal` returns http=404 in the 2xx-4xx pass range). Frontmatter status promoted to RESOLVED.
