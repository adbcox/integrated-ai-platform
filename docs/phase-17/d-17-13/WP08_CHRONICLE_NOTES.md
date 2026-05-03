# D-17-13 WP-08 chronicle — pending findings/notes

Scratchpad for WP-08 close. Promote into the canonical chronicle docs
(`docs/architecture-facts/integration-audit-doctrine.md`,
`docs/architecture-facts/local-tool-calling.md`,
`docs/architecture-facts/opnsense-dns-authority.md`) at WP-08 finalize.

## Finding 14 candidate — macOS mDNSResponder negative-response cache

**Surface:** Mac Mini consumer-side DNS resolution after Dnsmasq record
creation on OPNsense.

**Observation (2026-05-03, D-17-13 WP-03):** After adding the
`mac-studio.internal` Shape 1 host record via OPNsense Dnsmasq API,
the Mac Mini continued to fail to resolve the hostname for an extended
window:

- `dig mac-studio.internal @192.168.10.1` → 192.168.10.142 (correct)
- `dns-sd -q mac-studio.internal` → `0.0.0.0 No Such Record` (negative cache)
- `python3 -c "import socket; socket.gethostbyname('mac-studio.internal')"` → `gaierror: nodename nor servname provided`
- `curl http://mac-studio.internal:11434` → `Could not resolve host`
- `dscacheutil -flushcache` → no effect

**Root cause:** macOS `mDNSResponder` caches negative responses
(NXDOMAIN) independently from the legacy `DirectoryService` cache that
`dscacheutil` flushes. A query that landed pre-record-creation pins the
NXDOMAIN until the mDNSResponder cache TTL expires or the daemon is
HUP'd.

**Fix:** `sudo killall -HUP mDNSResponder` (interactive sudo required).

**Sub-doctrine — D-17-21 runbook addition:** when adding a `.internal`
record via OPNsense Dnsmasq, the runbook must include a downstream
consumer-side flush step on any macOS host that may have queried the
hostname pre-creation. Specifically:

```
# After adding host record on OPNsense:
sudo killall -HUP mDNSResponder    # macOS consumers
sudo systemd-resolve --flush-caches # systemd-resolved consumers (Linux)
# Linux nscd/dnsmasq-local: nscd -i hosts / systemctl restart dnsmasq
```

**Sibling-not-duplicate of D-17-21 doctrine:**
- D-17-21 = DNS *authority* surface (who answers `*.internal` — Dnsmasq sole authority).
- F14 = DNS *cache invalidation* surface (how consumers learn the answer changed).
- Both must be correct for end-to-end resolution to work post-record-add.

**Promote to:** `docs/architecture-facts/opnsense-dns-authority.md`
(new section "Consumer-side cache invalidation") + cross-reference in
`docs/architecture-facts/integration-audit-doctrine.md` Finding 14.

**Verified blocking case:** D-17-13 WP-03 Goose end-to-end smoke test
against `mac-studio.internal:11434` was blocked until operator ran
`sudo killall -HUP mDNSResponder` on Mac Mini.

## Other items pending for WP-08

- F1.B refinement: qwen3-coder:30b emits structured tool_calls in
  *streaming* mode via Ollama 0.22.1 — refines original F1
  (qwen2.5-coder via Ollama 0.20.7 streaming dropped tool_calls) along
  the (model-family × Ollama-version) axis. Promote to
  `docs/architecture-facts/local-tool-calling.md`.
- Framework script gap (operator-flagged backlog, NOT D-17-13 blocker):
  `roadmap-create.sh` lacks a `--reopen` mode for DONE → IN PROGRESS
  reopens on unblocker resolution. WP-08 should record this; not in
  scope to fix.
- CLAUDE.md execution-surface section: add Goose to the
  "execution-surface" mental model (Claude Code + Codex + Goose), with
  capability-boundary note (developer extension disabled in
  capability-validation phase).
- Capability-boundary chronicle: `goose-capability-boundary.md` —
  documents the disabled-extension list, the rationale ("no docker/
  ssh/Vault access initially"), and the Phase-A promotion gate (N>=5
  clean executions before re-enabling `developer`).
