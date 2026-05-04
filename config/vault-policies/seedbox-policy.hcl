# seedbox — read access to seedbox SFTP + rTorrent + SABnzbd credentials.
# D-17-76 (2026-05-04) — §18.L companion to D-17-49.
#
# Three distinct credential sets, separated by protocol/service (P2 doctrine):
#   secret/seedbox/sftp     — file-transfer (rclone/rsync moving completed
#                              downloads off the seedbox to QNAP)
#   secret/seedbox/rtorrent — torrent-client XML-RPC API (Cleanuparr
#                              download-client target on the rTorrent path)
#   secret/seedbox/sabnzbd  — Usenet-client REST api_key (platform-canonical
#                              Usenet client; consumers are non-Cleanuparr
#                              services such as Sonarr/Radarr direct
#                              integrations and future queue-monitor sidecars.
#                              Cleanuparr does NOT consume this path —
#                              Cleanuparr's deployed image binary does not
#                              implement SABnzbd as a download-client type;
#                              see docs/phase-18/d-17-49/SMOKE.md "Known
#                              limitation — Cleanuparr SABnzbd coverage gap".)
#
# Even when the seedbox uses the same login for SFTP and rTorrent (same
# host, same user), the paths stay separate so credentials can diverge later
# without policy changes. SABnzbd uses an api_key, distinct from password.

path "secret/data/seedbox/sftp" {
  capabilities = ["read"]
}

path "secret/data/seedbox/rtorrent" {
  capabilities = ["read"]
}

path "secret/data/seedbox/sabnzbd" {
  capabilities = ["read"]
}
