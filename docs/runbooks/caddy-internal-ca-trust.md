# Runbook: Trust the Caddy internal CA on client devices

**Last updated:** 2026-05-05 (D-17-115)

Caddy issues local certificates for `*.internal` hostnames from its own
internal root CA. That CA is not trusted by default on client devices, so
first-time access can show browser warnings or app TLS failures until the
root CA is installed.

## Cert provenance

The repo-canonical Caddy root CA is committed at:

| Field | Value |
|---|---|
| Repo path | `deployment/caddy/internal-root.crt` (TBD-PHASE-2 — D-17-115 Phase 2 commit pending) |
| Source command | `docker exec caddy cat /data/caddy/pki/authorities/local/root.crt` |
| Source host | Mac Mini at 192.168.10.145 (on-LAN access required) |
| Issuer DN | TBD-PHASE-2 (record at extraction time via `openssl x509 -in ... -noout -issuer`) |
| Subject DN | TBD-PHASE-2 (typically `CN=Caddy Local Authority - <year> ECC Root`) |
| SHA-256 fingerprint | TBD-PHASE-2 (record via `openssl x509 -in ... -noout -fingerprint -sha256`) |
| Validity | ~10 years from Caddy first-run on the host |
| Rotation tracking | KI-012 (`docs/known-issues/KI-012-caddy-ca-rotation.md`) |

The `TBD-PHASE-2` markers are fill-in points for the next on-LAN session
— operator extracts the cert on Mac Mini, commits it to the repo path,
captures fingerprint + issuer DN via openssl, and replaces the markers
via search-and-replace. Until that happens, scripts that reference
`deployment/caddy/internal-root.crt` (e.g. `scripts/caddy-ca-trust-macos.sh`)
fail-fast at their cert-file existence check.

## Canonical CA export

The current root certificate is exported from the Caddy container:

```bash
docker exec caddy cat /data/caddy/pki/authorities/local/root.crt > /tmp/caddy-root.crt
```

For convenience, this repo session also copied the file to:

```text
/Users/admin/Library/Application Support/iap/caddy-root.crt
```

The file contents are identical.

## macOS

1. Open `/tmp/caddy-root.crt` or `/Users/admin/Library/Application Support/iap/caddy-root.crt`.
2. Import it into **Keychain Access**.
3. Choose the **System** keychain.
4. Open the certificate details and set **Trust** to **Always Trust**.
5. Re-open `https://plex.internal` or any other `*.internal` site.

## Scripted distribution (macOS)

`scripts/caddy-ca-trust-macos.sh` automates the manual macOS procedure
above. Prerequisites: cert file at `deployment/caddy/internal-root.crt`
(D-17-115 Phase 2 — see §"Cert provenance") and macOS host with `sudo`
available.

Invocation:

```bash
./scripts/caddy-ca-trust-macos.sh
# or with explicit cert path:
./scripts/caddy-ca-trust-macos.sh /path/to/root.crt
```

The script is idempotent — re-running on a device that already has a
matching `Caddy Local Authority` cert in the System keychain prints a
notice and exits 0 without re-prompting for sudo. Note: the idempotency
check matches CN substring, not fingerprint, so after a CA rotation
event (KI-012) operator must remove the old cert from the System
keychain via Keychain Access before re-running. See §"Re-trust
procedure" for the full rotation-event response.

Exit codes:

| Code | Meaning |
|---|---|
| 0 | Trust install succeeded OR cert already trusted (idempotent no-op) |
| 1 | Generic failure |
| 2 | Cert file not found at expected path |
| 3 | Not running on macOS (uname -s != Darwin) |
| 4 | sudo not available in PATH |
| 5 | Post-install verification failed |

Source: `scripts/caddy-ca-trust-macos.sh`. Linux distribution is a
separate deliverable deferred until Threadripper / Ryzen OS choice is
confirmed.

## iPhone / iPadOS

1. AirDrop `caddy-root.crt` to the device, or place it in Files and open it there.
2. Install the profile when prompted.
3. Go to **Settings → General → VPN & Device Management** and confirm the profile is installed.
4. Go to **Settings → General → About → Certificate Trust Settings** and enable full trust for the Caddy root certificate.
5. Re-test `https://plex.internal`.

## Apple TV

tvOS does not have the same easy AirDrop workflow as iOS. Use one of:

1. Apple Configurator 2 from a Mac to install a profile.
2. An MDM profile if the device is managed.

Then verify `https://plex.internal` or the relevant `*.internal` service from the Apple TV app surface.

## Android

1. Copy `caddy-root.crt` to the device.
2. Open **Settings → Security → Encryption & credentials**.
3. Choose **Install a certificate**.
4. Select **CA certificate** and install the Caddy root certificate.

## Verification

After trust installation, the client should load `https://plex.internal`
without browser certificate warnings and should allow Plex apps to connect
cleanly.

If a device still warns after trust import, verify:

1. The device imported the current Caddy root, not an older copy.
2. The device trusts the **System** store on macOS.
3. The service hostname is `*.internal`, not `plex-mcp.internal`.

### Per-device verification checklist

Trust install must be verified on each device that consumes
`*.internal` services. Phase 1 of D-17-115 establishes the checklist;
Phase 2 fills in verification dates per device.

| Device class | Device | Status |
|---|---|---|
| macOS | Mac Mini (control plane, runs Caddy) | PENDING — Phase 2 verification |
| macOS | Mac Studio (compute node) | PENDING — Phase 2 verification |
| macOS | MacBook Pro (current primary work surface) | PENDING — Phase 2 verification |
| iOS | iPhone | PENDING — Phase 2 verification |
| iPadOS | iPad | PENDING — Phase 2 verification |
| tvOS | Apple TV | PENDING — Phase 2 verification |
| Android | Android device | PENDING — Phase 2 verification |

At Phase 2 close, each PENDING entry flips to `verified-on-YYYY-MM-DD`
with a note if verification surfaced any device-specific friction.

## Re-trust procedure

Re-trust is required when:

- Caddy CA rotation is observed (next event ~2035-2036; tracked as
  KI-012).
- A fresh cert extraction surfaces a SHA-256 fingerprint different
  from the one recorded in §"Cert provenance".
- The Caddy container's data directory was reset (e.g.,
  `/data/caddy/pki/` removed during a recovery procedure), which
  forces Caddy to regenerate the root.

Steps:

1. Re-extract the cert per §"Canonical CA export"
   (`docker exec caddy cat ... > deployment/caddy/internal-root.crt`).
2. Recompute fingerprint + issuer DN via
   `openssl x509 -in deployment/caddy/internal-root.crt -noout -issuer -fingerprint -sha256`.
   Update §"Cert provenance" with the new values.
3. Commit the new `deployment/caddy/internal-root.crt` + the runbook
   provenance update.
4. On each macOS device: remove the old `Caddy Local Authority` cert
   from the System keychain via Keychain Access (the script's
   idempotency check matches CN substring, not fingerprint, so without
   removal it will skip-as-already-trusted and the rotation will
   silently fail to take effect). Then re-run
   `scripts/caddy-ca-trust-macos.sh`.
5. On iOS / iPadOS / Apple TV / Android, manually re-import the new
   cert per the per-class procedures above.
6. Update §"Per-device verification checklist" with the re-verification
   dates.

See `docs/known-issues/KI-012-caddy-ca-rotation.md` for rotation
tracking and the option-(b) / option-(c) decision tree.

## Cross-references

- `docs/architecture-facts/caddy-internal-tls-doctrine.md`
- `docs/architecture-facts/media-stack-doctrine.md`
- `docs/runbooks/opnsense-add-host-overrides.md`
- `docker/caddy/Caddyfile`
