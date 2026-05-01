# Vault policy for Restic backup AppRole.
# Allows read access to credentials needed by scripts/backup.sh:
#   - secret/restic/backup    : password, repository
#   - secret/minio/backup     : access_key, secret_key
#
# Re-provisioned 2026-05-01 after the 2026-04-30 KV-loss incident
# wiped the original backup AppRole + policy.
# Closes audit R-01 / D-15-03.

path "secret/data/restic/backup" {
  capabilities = ["read"]
}

path "secret/data/minio/backup" {
  capabilities = ["read"]
}
