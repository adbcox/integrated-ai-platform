# Remote Work Recovery (Singapore Window)

Last updated: 2026-05-03 (D-17-52 WP-05)

## Scope

Recovery paths if remote access fails while traveling.

Primary path:
- Headscale tailnet + subnet-router route (`192.168.10.0/24`) on macmini

Independent fallback path:
- OPNsense WireGuard VPN (separate control plane / separate failure mode)

## Failure matrix

1. **MacBook cannot reach tailnet at all**
- Symptom: `tailscale status` disconnected / no peers.
- Action:
  - Toggle network (Wi-Fi -> cellular tether).
  - `sudo tailscale down && sudo tailscale up --login-server ...`
  - If still down, use OPNsense WireGuard fallback.

2. **Tailnet connected, but `.internal` domains fail**
- Symptom: SSH by tailnet IP works, `prowlarr.internal` fails.
- Cause: subnet-router route missing or not accepted.
- Action:
  - Check route is advertised/approved on Headscale.
  - Check MacBook joined with `--accept-routes=true --accept-dns=true`.
  - Temporary fallback: direct tailnet IP + port.
  - If unresolved, use OPNsense WireGuard fallback and LAN DNS path.

3. **Headscale container down on macmini**
- Symptom: all tailnet clients lose control-plane refresh; new joins fail.
- Action:
  - Use OPNsense WireGuard as out-of-band path.
  - SSH to macmini via WireGuard path and recover Headscale container:
    `docker compose -f ~/repos/integrated-ai-platform/docker/headscale/docker-compose.yml up -d`
  - Validate:
    `docker ps | rg headscale`
    `docker exec headscale headscale nodes list`

4. **OPNsense DNS reachable only via LAN, not tailnet**
- Symptom: tailnet connected but `dig @192.168.10.1 ...` timeout.
- Action:
  - Confirm macmini subnet-router route is active + approved.
  - If route path broken, use WireGuard fallback and continue work until repaired.

## OPNsense WireGuard fallback (critical)

This is the independent recovery path if Headscale itself fails.

Precondition before departure:
- WireGuard profile is already configured on MacBook and tested from cellular.

When needed:
1. Connect WireGuard on MacBook.
2. Verify tunnel IP assigned.
3. SSH to macmini over LAN IP (or internal DNS) through WireGuard.
4. Restart/repair Headscale and validate route advertisement.

## Minimal emergency command pack (MacBook)

```bash
# Headscale status
/opt/homebrew/bin/tailscale status

# Test ssh directly to macmini tailnet IP alias
ssh macmini-tailnet 'hostname; date'

# DNS path through OPNsense
dig @192.168.10.1 prowlarr.internal +short

# HTTP path
curl -skI https://prowlarr.internal | head -n 1
```

## Notes

- Headscale and WireGuard must not share the same single point of failure assumptions.
- If both fail, recovery requires physical/local intervention at home site.
