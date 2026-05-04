# MacBook Headscale Enrollment (Travel Readiness)

Last updated: 2026-05-03 (D-17-52 WP-03)

## Purpose

Join the operator MacBook to the self-hosted Headscale tailnet so remote
work from foreign networks can reach the Mac Mini control plane.

## Constraints

- Run MacBook commands on the MacBook directly (operator-managed host).
- Do not copy credentials into notes/chat.
- Use one-time/short-lived auth keys where possible.

## 1) Install Tailscale client on macOS (operator-run)

```bash
curl -fsSL https://pkgs.tailscale.com/stable/tailscale-setup-latest.pkg -o /tmp/tailscale.pkg
sudo installer -pkg /tmp/tailscale.pkg -target /
```

Verify CLI exists:

```bash
/opt/homebrew/bin/tailscale version
```

## 2) Create/consume pre-auth key (macmini + MacBook)

Generate a short-lived reusable key on Mac Mini:

```bash
docker exec headscale headscale preauthkeys create \
  --user admin \
  --reusable=true \
  --expiration 24h
```

On MacBook, join Headscale:

```bash
sudo tailscale up \
  --login-server http://headscale.internal:8080 \
  --authkey <hskey-auth-...> \
  --accept-routes=true \
  --accept-dns=true
```

Notes:
- `--accept-routes=true` is required for subnet-router option in WP-04.
- `--accept-dns=true` allows Headscale DNS settings to apply.

## 3) Verify node enrollment (macmini)

```bash
docker exec headscale headscale nodes list
```

Expected: MacBook appears with a `100.x.y.z` tailnet address and `Connected=true`.

## 4) Post-enrollment verification (MacBook)

```bash
/opt/homebrew/bin/tailscale status
/opt/homebrew/bin/tailscale ip -4
scutil --dns | rg -n 'nameserver|search domain'
```

Connectivity checks:

```bash
ping -c 3 100.x.y.z          # macmini tailnet IP
ssh admin@100.x.y.z          # or alias, see step 5
```

## 5) SSH convenience alias (MacBook)

Add to `~/.ssh/config` on MacBook:

```sshconfig
Host macmini-tailnet
  HostName 100.x.y.z
  User admin
  ServerAliveInterval 30
  ServerAliveCountMax 3
```

Then connect with:

```bash
ssh macmini-tailnet
```

## 6) Foreign-network simulation (night-before test)

Use iPhone hotspot/cellular tether (not LAN Wi-Fi):

1. Disconnect MacBook from home LAN.
2. Connect via cellular hotspot.
3. Confirm Tailscale shows connected.
4. Run:

```bash
ssh macmini-tailnet 'hostname; date'
curl -skI https://headscale.internal | head -n 1
curl -skI https://prowlarr.internal | head -n 1
```

Expected:
- SSH succeeds.
- `.internal` checks succeed once WP-04 DNS option is implemented.

## Failure signatures

- `nodes list` empty or no MacBook entry: enrollment failed; re-run step 2.
- SSH works by tailnet IP but `.internal` fails: DNS/routing gap (WP-04 unresolved).
- Tailnet disconnects intermittently on cellular: keepalive/reconnect issue; test again with another network before departure.
