# arr-stack authentication doctrine (D-17-98)

## Canonical posture

For Sonarr/Radarr/Lidarr/Prowlarr, the canonical operator posture is:

- `AuthenticationRequired=DisabledForLocalAddresses`
- Internal LAN access (`*.internal`, via Caddy front on 192.168.10.145): no login prompt
- External/untrusted source address: authentication required

`AuthenticationMethod` is service-specific and may remain:

- Sonarr: `Basic`
- Radarr: `Forms`
- Lidarr: `Forms`
- Prowlarr: `Forms`

Do not use `AuthenticationMethod=None` with `AuthenticationRequired=Enabled`; this is a contradictory state and can block normal UI access patterns.

## Credentials discipline

Lidarr/Sonarr/Radarr/Prowlarr credentials must exist in Vault under:

- `secret/arr/lidarr`
- `secret/arr/sonarr`
- `secret/arr/radarr`
- `secret/arr/prowlarr`

Expected fields:

- `username`
- `password`
- existing non-auth fields (for example `api_key`) must be preserved

Write/verify policy:

- Use `vault kv patch` to avoid clobbering existing fields
- Hash-only verification in logs/transcripts (no plaintext credential echo)

## Bazarr note

Bazarr does not use the same `AuthenticationRequired` enum from the *arr XML config model. Its auth posture is controlled via Bazarr-specific `auth` settings in `config.yaml`. Treat Bazarr as adjacent but not identical for this doctrine.
