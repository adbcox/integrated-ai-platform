# Runbook: Add OPNsense Host Overrides for `.internal` Services

**Last updated:** 2026-05-03 (D-17-47 WP-02)

## Scope

Use this when a new Caddy-fronted internal service is added (for example
`bazarr.internal`) and needs LAN DNS resolution.

## Authority

- `.internal` authority is **Unbound DNS** on OPNsense port `53`.
- Dnsmasq may run for other host records, but `.internal` overrides must be
  added in Unbound Host Overrides.

## Procedure

1. Open OPNsense web UI (`https://192.168.10.1`).
2. Navigate to `Services` -> `Unbound DNS` -> `Overrides` -> `Host Overrides`.
3. Click `+` and create the record:
- `Host`: short host name (example: `bazarr`)
- `Domain`: `internal`
- `Type`: `A`
- `IP`: `192.168.10.145` (Mac Mini / Caddy front)
- `Description`: short note (example: `Caddy front`)
4. Save, then apply/reload Unbound.

## Verification

Run from Mac Mini:

```bash
dig @192.168.10.1 -p 53 bazarr.internal +short
```

Expected: `192.168.10.145`

Then verify HTTPS route:

```bash
curl -skI https://bazarr.internal | head -n 1
```

Expected: `HTTP/2 200` or `HTTP/2 302`

## Current arr-stack host override set

Add these records when deploying media automation siblings:

- `bazarr.internal` -> `192.168.10.145`
- `cleanuparr.internal` -> `192.168.10.145`
