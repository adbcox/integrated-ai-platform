# Caddy internal TLS doctrine (D-17-115)

## Canonical posture

Caddy is the LAN TLS terminator for `*.internal` hostnames on this platform.
It issues certificates from its own internal root CA. That CA is valid for the
platform, but client devices must trust it explicitly before browser warnings
or TLS app failures disappear.

## Distribution rule

Any new LAN client that needs to use `https://*.internal` must receive the
current Caddy root CA certificate and have it trusted locally.

Canonical export path:

- `/tmp/caddy-root.crt`
- `/Users/admin/Library/Application Support/iap/caddy-root.crt`

The source of truth is the certificate inside the Caddy container:

- `docker exec caddy cat /data/caddy/pki/authorities/local/root.crt`
- Repo-canonical (D-17-115 Phase 2 cert commit pending): `deployment/caddy/internal-root.crt` for cert content; `scripts/caddy-ca-trust-macos.sh` for scripted macOS trust install; `docs/runbooks/caddy-internal-ca-trust.md` for manual procedures on other OS classes (iOS / iPadOS / tvOS / Android). Rotation tracked in `docs/known-issues/KI-012-caddy-ca-rotation.md`.

## Device classes

- macOS: import into Keychain Access and trust in the System keychain.
- iOS / iPadOS: install as a profile, then enable certificate trust in Settings.
- Apple TV: use Apple Configurator 2 or MDM profile distribution.
- Android: install as a CA certificate through Security settings.

## Naming discipline

Trust distribution applies to the canonical service hostname, not to adjacent
control surfaces.

- `plex.internal` = Plex Media Server on QNAP
- `plex-mcp.internal` = Plex MCP control surface on the Mac Mini

## Operational consequence

If a new client cannot open `https://plex.internal` without warnings, the
problem is usually missing CA trust on that client, not a server defect.
