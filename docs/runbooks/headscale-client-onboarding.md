# Headscale client onboarding

Procedure for joining a new Mac/Linux node to the platform's
Headscale-managed VPN. Headscale itself runs in a container on
Mac Mini (`headscale.internal`). Each node runs the Tailscale
client pointed at this self-hosted Headscale server.

## Operator-side actions

Tailscale install requires sudo and the operator's password on the
target node. Per CLAUDE.md operator-side-actions doctrine, this is
NOT executed via SSH from Claude Code or any automation. The
operator runs steps 1-3 below directly on the target node.

### 1. Install Tailscale (target node)

On the target node (e.g., Mac Studio at 192.168.10.142):

```
# macOS — download and run installer:
curl -fsSL https://pkgs.tailscale.com/stable/tailscale-setup-latest.pkg -o /tmp/tailscale.pkg
sudo installer -pkg /tmp/tailscale.pkg -target /
```

For Linux nodes, follow upstream instructions at
https://tailscale.com/kb/installation. The Headscale server
URL in step 2 is the same regardless of OS.

### 2. Authenticate against Headscale (target node)

```
sudo tailscale up --login-server=http://headscale.internal:8080
```

Tailscale prints a URL with a one-time pre-auth token in the path.
The CLI will hold the connection open waiting for approval.

### 3. Approve the device (Mac Mini, in another terminal)

From Mac Mini, list pending devices:

```
docker exec headscale headscale nodes list
```

Approve by node ID:

```
docker exec headscale headscale nodes register --user <username> --key <node-key>
```

(The exact command depends on whether the node used pre-auth or
machine-key registration — Headscale CLI will print the right
form when you run `headscale help nodes`.)

### 4. Verify connectivity

From the target node, ping another node by Tailscale name:

```
tailscale status
ping 100.x.y.z          # Tailscale IP of an already-joined node
```

Expected: ICMP replies via the Tailscale interface
(`utun*` on macOS).

## Per-node history

| Node | Date | Status | Notes |
|---|---|---|---|
| mac-mini | (Phase 13) | Done | Headscale server itself; runs in `headscale` container |
| mac-studio | 2026-05-01 | Pending operator install | Onboarded via 17.O Day-1; Tailscale install + Headscale approval pending |

When a node onboards, append a row above. Don't delete completed
rows — the table is the audit trail.

## Troubleshooting

- **`tailscale up` hangs forever waiting for approval**: confirm
  the Headscale container is healthy (`docker ps | grep headscale`)
  and the Mac Mini's Caddy site for `headscale.internal` resolves
  from the target node (`curl http://headscale.internal:8080/health`).

- **Approved but no Tailscale IP appears**: check Headscale logs
  (`docker logs headscale --tail 50`). If the node-key was rejected,
  re-run `tailscale up` to generate a fresh key.

- **Tailscale IP works but DNS doesn't resolve other nodes**: MagicDNS
  is configured per-Headscale-namespace; if the platform's namespace
  doesn't have it enabled, use Tailscale IPs directly. MagicDNS
  enablement is a Headscale server-side config change, not a client
  one.

## Related

- `docs/PHASE_ROADMAP.md` Phase 18.B (Linux/Threadripper) — same
  procedure when Threadripper joins
- `docs/runbooks/mac-studio-day-1.md` — Day-1 onboarding context
