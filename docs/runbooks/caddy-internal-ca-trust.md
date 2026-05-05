# Runbook: Trust the Caddy internal CA on client devices

**Last updated:** 2026-05-05 (D-17-115)

Caddy issues local certificates for `*.internal` hostnames from its own
internal root CA. That CA is not trusted by default on client devices, so
first-time access can show browser warnings or app TLS failures until the
root CA is installed.

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

## Cross-references

- `docs/architecture-facts/caddy-internal-tls-doctrine.md`
- `docs/architecture-facts/media-stack-doctrine.md`
- `docs/runbooks/opnsense-add-host-overrides.md`
- `docker/caddy/Caddyfile`
