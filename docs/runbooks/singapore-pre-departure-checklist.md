# Singapore Pre-Departure Checklist (Night Before Travel)

Last updated: 2026-05-03 (D-17-52 WP-06)

## Pass criteria

All checks below pass from MacBook on cellular tether (foreign-network simulation).

## A. MacBook enrollment (operator)

- [ ] `tailscale` installed and logged into Headscale per
      `docs/runbooks/macbook-headscale-enrollment.md`
- [ ] `tailscale status` shows macmini peer

## B. macmini subnet-router (operator one-time privileged step)

Run on macmini host terminal:

```bash
sudo /opt/homebrew/bin/tailscale up \
  --login-server http://headscale.internal:8080 \
  --authkey <hskey-auth-...> \
  --advertise-routes=192.168.10.0/24 \
  --accept-dns=true
```

Then approve route on Headscale (macmini):

```bash
docker exec headscale headscale nodes list-routes
# approve route for macmini node id + advertised 192.168.10.0/24 route:
docker exec headscale headscale nodes approve-routes --identifier <node-id> --routes 192.168.10.0/24
docker exec headscale headscale nodes list-routes
```

## C. Foreign-network simulation (MacBook on phone hotspot)

- [ ] Disconnect from home Wi-Fi.
- [ ] Connect to iPhone hotspot/cellular tether.
- [ ] Confirm tailnet connected:

```bash
/opt/homebrew/bin/tailscale status
```

- [ ] SSH to macmini over tailnet:

```bash
ssh macmini-tailnet 'hostname; date'
```

- [ ] DNS through OPNsense:

```bash
dig @192.168.10.1 prowlarr.internal +short
```

- [ ] HTTPS via internal domain:

```bash
curl -skI https://prowlarr.internal | head -n 1
```

- [ ] Codex/Claude flow end-to-end via SSH:
  - Start SSH session to macmini.
  - Run one Codex CLI command in repo.
  - Confirm git status/commit visibility from remote shell.

## D. Out-of-band fallback (WireGuard)

- [ ] OPNsense WireGuard profile present on MacBook.
- [ ] WireGuard tunnel connects from cellular.
- [ ] SSH to macmini works over WireGuard path (independent of Headscale).

## E. Recovery artifacts present

- [ ] `docs/runbooks/remote-work-recovery.md` reviewed.
- [ ] Headscale container healthy:

```bash
docker ps --format '{{.Names}} {{.Status}}' | rg '^headscale '
docker exec headscale headscale nodes list
```

## Stop/No-Go

If any of B/C/D fails, travel readiness is NO-GO until resolved.
