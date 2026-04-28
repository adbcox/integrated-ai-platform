# KI-003: obot's UI returns 502 on /

## Status
PRE-EXISTING — separate from Phase 7 routing

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
