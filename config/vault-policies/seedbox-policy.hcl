# seedbox — read access to seedbox SFTP + qBittorrent WebUI credentials.
# D-17-76 (2026-05-04) — §18.L companion to D-17-49.
#
# Two distinct credential sets, separated by protocol:
#   secret/seedbox/sftp        — file-transfer (rclone/rsync moving completed
#                                 downloads off the seedbox to QNAP)
#   secret/seedbox/qbittorrent — torrent-client WebUI API access (Cleanuparr
#                                 Queue/Download Cleaner modules)
#
# Even when the seedbox uses the same login for both protocols, the paths
# stay separate so credentials can diverge later without policy changes.

path "secret/data/seedbox/sftp" {
  capabilities = ["read"]
}

path "secret/data/seedbox/qbittorrent" {
  capabilities = ["read"]
}
