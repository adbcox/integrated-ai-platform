# macOS firewall / Local Network privacy interactions with Homebrew binaries

Status: Active doctrine. Recorded 2026-05-01 during D-16-04 T6.

## Symptom

Homebrew Go binaries (restic, victoria-metrics, others) report
"connect: no route to host" or `ENETUNREACH` despite `curl`/`nc`
succeeding to the same `host:port` from the same shell.

## Diagnostic journey for D-16-04 T6

Three wrong hypotheses, then the correct one:

1. **PATH issue** (wrong) — initial assumption that `restic` was not on
   cron's PATH. Disproven: restic resolves correctly under SSH.
2. **macOS Application Firewall blocking adhoc-signed binaries** (wrong)
   — explicit allowlist via `socketfilterfw` had no effect.
   `socketfilterfw` is INCOMING ONLY; outbound is governed by a
   different subsystem.
3. **macOS Tahoe Local Network privacy** (wrong) — would have blocked
   plain SSH sessions equally. It didn't. Hypothesis refuted by the
   control window successfully running restic from a non-VS-Code SSH
   session.
4. **CORRECT: VS Code Remote SSH was port-forwarding `*:9000` from
   MacBook to Mac Mini**, intercepting `restic→MinIO` traffic. Closing
   VS Code released the forwarding; backup completed in <1 second.

## Real cause

VS Code Remote SSH's auto-port-forwarding aggressively forwards ports
it detects in active connections. The Mac Mini ended up listening on
`*:80`, `*:443`, `*:8080`, AND `*:9000` — all owned by the SSH process
that the VS Code Server spawned. When restic tried to reach
`192.168.10.201:9000`, the connection was intercepted (mechanism not
fully traced, but kernel-level routing or macOS PF rules are likely).

## Diagnosis evidence

- `codesign -dvv /opt/homebrew/bin/restic` shows `Signature=adhoc` —
  but this is NOT the cause; many adhoc binaries work fine on this
  system
- `lsof -nP -iTCP -sTCP:LISTEN` shows `ssh` process owning unexpected
  ports
- restic from plain Terminal.app SSH (no VS Code) → works
- restic from VS Code Remote SSH session → hangs on connect to LAN
  services
- Closing VS Code application releases the SSH-owned port-forwards

## Remediation

1. For interactive runs: don't run network-heavy CLI commands from VS
   Code's integrated terminal if VS Code Remote SSH is forwarding
   ports that conflict with the target service.
2. For backup operations: cron and operator manual sessions are
   unaffected (no VS Code involvement); production path is clean.
3. To audit VS Code's port forwarding: check `~/.ssh/config` on the
   CLIENT machine for `RemoteForward` directives, AND check VS Code
   settings: `remote.SSH.defaultForwardedPorts` and
   `remote.autoForwardPorts` (default behavior is too eager).

## Prevention

Long-term: restrict VS Code's auto-port-forwarding via the client's
`settings.json`: `{ "remote.autoForwardPorts": false }` — this turns
off the magic and makes port forwarding explicit. Some convenience
lost, much surprise prevented.

## Affected binaries on this platform

Currently: `restic` (when invoked from VS Code-spawned shells).
Add others here as they're discovered.
