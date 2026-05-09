# D-17-137 Personal Briefing Engine: Sink Decision Tradeoff Matrix

**Status:** PENDING DECISION
**Date authored:** 2026-05-09 (feat/rss-intelligence branch)
**Source of truth:** Operator enumeration KI-B-02 (four candidate sinks); substrate doctrine cross-reference
**Consumer:** D-17-137 (Personal Briefing Engine)
**Related:** D-17-136 (Technical Intelligence RSS — sink is locked to OpenProject)

## Decision Frame

D-17-137 generates daily briefing cards (source-linked, perspective-diverse, personal-relevance ranked) via Ollama summarization of curated RSS feeds. Unlike D-17-136 (which outputs to OpenProject WPs), D-17-137's sink is operator-chosen based on how the operator consumes personal briefings. This matrix compares four candidates across nine axes to inform that choice.

## Comparison Matrix

| Axis | Obsidian Vault | Nextcloud | OpenProject | Daily Email |
|---|---|---|---|---|
| **Latency** | Push to watched folder; immediate in-editor availability (seconds) | Push via WebDAV; seconds to appear on mobile/web (sync lag ~5–30s) | Push via API; instant in OpenProject (seconds); integrates with D-17-136 output | Pull-based; cards appear in inbox at scheduled time (daily morning, e.g., 06:00) |
| **Cross-device access** | Obsidian Sync (paid, ~$100/yr) or manual sync; local-first, requires client; mobile via app | Native: web, mobile app, desktop. Syncs via server; no client required on web. | Native: web, mobile app, desktop. Syncs via OpenProject; same auth as D-17-136. | Web (Gmail/Outlook etc.); mobile email client. Largest device coverage. |
| **Search affordance** | Full-text + tags + Markdown metadata. Local search in editor; AI-powered via Obsidian plugins (optional). Portable (Markdown). | Full-text search in Nextcloud UI; limited structured query. Markdown readable but not optimized for extraction. | Structured query (OpenProject search syntax). Full-text. Tag/category filters. Same UX as D-17-136. | Thread-based search in email client (Gmail, Outlook). Limited to subject/sender/date. |
| **Backup story** | Obsidian Sync handles versioning; OR manual backup of vault to MinIO (already available per D-17-37 substrate). Zero new infrastructure. | Nextcloud built-in snapshot/versioning; independent of Restic/MinIO. New infrastructure (Nextcloud) handles its own backups. | OpenProject backups independent; covered by existing D-17-136 OpenProject deployment. Zero new infrastructure. | Email provider's backup (Gmail, Outlook). Operator has no direct control; depends on email provider SLA. |
| **Privacy / data location** | Local vault on operator's Mac Mini/Studio. Encrypted on disk. Optional Obsidian Sync keeps copy on Obsidian's servers. Data remains operator-controlled. | Nextcloud server (QNAP, operator's infrastructure, or self-hosted VM). End-to-end encryption available. Data stays on operator's hardware or trusted server. | OpenProject server (self-hosted or operator-provisioned). Data on operator's infrastructure or OPM-hosted instance. | Email provider servers (Google, Microsoft, self-hosted). Data leaves operator's infrastructure (email providers not bound by platform doctrine). |
| **Integration friction (Python fetcher → sink)** | File write to watched folder (simplest). Fsnotify triggers Obsidian re-index. Single-digit lines of Python code. | WebDAV PUT (HTTP-based, mature). Python libraries: `webdav3` or similar. Moderate complexity; requires Nextcloud server auth (credentials). | REST API (same API as D-17-136 technical digest). OpenProject Python client available. Consistent with D-17-136 integration. | SMTP (mature). Python `smtplib` or `email` module. ~20 lines of code. Requires SMTP relay (local or external). Simplest protocol but no return channel. |
| **Operator's existing usage pattern** | If already a heavy Obsidian user: natural fit. Vault already exists; briefings live alongside notes/research. | If Nextcloud already deployed for Photos/Calendar: fits existing workflow. Additive layer. If not deployed: new infra. | If OpenProject already used for D-17-136: same UX, no new tool learning. D-17-136 and D-17-137 output coexist naturally. | If Gmail/Outlook primary daily interface: briefing digest arrives in the flow. No new app needed. |
| **Failure modes** | Obsidian down: Python fetcher still writes files; operator must manually trigger re-index. Obsidian Sync fails: vault still writable locally. **Concern:** versioning/sync loss if Sync outage + local edits collide. | Nextcloud down: briefing write fails; alerts fire; operator manually retries. WebDAV auth failure: write blocked until credentials fixed. Mobile/web access blocked until Nextcloud back. | OpenProject down: API write fails; alerts fire. Operator falls back to D-17-136 briefing in OpenProject comment. Same SLA/OKR as D-17-136. | Email down: briefing queues in SMTP relay; retries 24–48h. Email provider outage: cards stuck in queue. **Concern:** email not guarantee delivery if provider down (not operator's hardware). |
| **Reversibility** | Easy. Cards are Markdown files; export vault as-is. Switch to Nextcloud: move files via export. Obsidian Sync can be disabled at any time. Archive accessible always. | Easy. Export to Markdown or PDF. Cards live in Nextcloud as files or notes (depends on app choice). Move to Obsidian: export Markdown, import. Nextcloud can be decommissioned. | Easy. Tickets exportable via OpenProject API. Cards are structured data (title, summary, source, perspective scores). Can be exported to Markdown + metadata JSON. OpenProject can be decommissioned. | Difficult. Emails are immutable once sent; recipients hold copies. Cards in email archive (operator's email provider controls retention). Switching sinks means new emails prospectively; prior cards stuck in email client. Lowest reversibility. |

## Per-Candidate Summaries

- **Obsidian Vault:** Best for operators who live in note-taking; seamless integration with research/PKM workflow; local-first privacy; no new infrastructure. Friction: Sync reliability, cross-device story weaker than Nextcloud.

- **Nextcloud:** Best for operators who want device-agnostic access (phone, laptop, web) without leaving personal infrastructure; natural fit if Nextcloud already serves Photos/Calendar. Friction: new infra to run (or external hosting); WebDAV integration adds one more layer.

- **OpenProject:** Best for operators who want D-17-136 and D-17-137 output coexisting in same UX; operational simplicity (same team, same API, same SLA). Friction: reuses a system meant for structured work (technical WPs); briefing cards less structured than technical digests.

- **Daily Email Digest:** Best for operators with email as primary interface; largest device coverage (any email client); simplest Python integration (SMTP). Friction: lowest reversibility; no structured query; email provider controls data; no true local-first privacy.

## Recommendation Framing

This matrix favors **Obsidian** and **Nextcloud** for operators prioritizing privacy, reversibility, and integration with personal infrastructure. **OpenProject** is justified for operators who value operational coherence (same system as D-17-136). **Email** is justified only if email is the operator's exclusive interface and simplicity outweighs archive concerns.

**Decision pending operator selection (KI-B-02).**

## Cross-references

- `docs/architecture-facts/rss-intelligence-substrate-doctrine.md` — substrate doctrine
- `docs/PROJECT_FRAMEWORK.md` D-17-137 — Personal Briefing Engine (sink decision noted as pending operator input)
- D-17-37 — artifact storage substrate (Restic/MinIO backup available for Obsidian/Nextcloud files)
- Master log Section 17 (Roca-style Personal Briefing Engine, 2026-05-06)
