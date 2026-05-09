# RSS Aggregator Comparison: Miniflux vs FreshRSS

**Status:** ACTIVE
**Date authored:** 2026-05-09 (continuation of feat/rss-intelligence branch, Tokyo travel session)
**Source of truth:** Official Miniflux and FreshRSS project documentation, READMEs, and releases (cited inline)
**Consumers:** D-17-136 (Technical Intelligence RSS), D-17-137 (Personal Briefing Engine)
**Substrate references:** `rss-intelligence-substrate-doctrine.md`

## Purpose

This document rigorously compares Miniflux and FreshRSS along all material axes to defend the substrate doctrine's "Miniflux default, FreshRSS strong alternative" recommendation and document the conditions under which an operator would legitimately choose one over the other.

## Comparison Table

| Axis | Miniflux | FreshRSS |
|---|---|---|
| **License + ethos** | Apache 2.0 (permissive OSS). Single-author (Frédéric Guillot), opinionated about simplicity over feature breadth. | GNU AGPL 3.0 (copyleft OSS). Community-maintained, multi-maintainer. Values customization and extensibility. |
| **Implementation language / runtime** | Go (87% of codebase). Single statically-compiled binary; no external runtime dependencies. | PHP 8.1+ (80% of codebase). Requires web server (Apache 2.4+, nginx, lighttpd) and PHP extensions (cURL, DOM, JSON, XML, session, ctype). |
| **Footprint (idle)** | ~2–5 MB RAM (stated: "couple of MB" even with hundreds of feeds). Negligible CPU. Single binary (~15 MB executable, exact size varies by platform). | Lightweight PHP app. Documented to run on Raspberry Pi 1 with <1 second response time (estimated ~15–50 MB RAM depending on feed count; not formally stated). |
| **Database backend (default + alternatives)** | PostgreSQL exclusively. No option for SQLite, MySQL, or other backends. Requires PostgreSQL 10+. | Multiple options: PostgreSQL 10+, SQLite, MariaDB 10.6+, MySQL 8.0+. Default is typically SQLite for single-user installs. |
| **Update polling model** | Internal scheduler (background process) or traditional cron job. Default polling interval: 1 hour. Respects HTTP cache headers (Last-Modified, ETags, Cache-Control). | WebSub-capable (instant push from compatible sources: Friendica, WordPress, Blogger, Medium). Fallback to polling (interval configurable). Respects cache headers. |
| **API surface** | REST API (first-class; Python and Go client libraries available). Fever API (compatibility). Google Reader API (compatibility). Webhooks for custom integrations. | Google Reader API (recommended primary). Fever API (compatibility). 20+ mobile/desktop apps accessible via these APIs. No native REST API. |
| **UI quality** | Excellent. Minimalist, distraction-free, responsive across desktop/tablet/mobile. 6 theme variants (Light/Dark × Sans/Serif, plus System variants). Keyboard shortcuts, optional touch gestures. Explicitly designed for content focus. | Good. Functional, responsive, multi-language UI (20+ languages at 80%+ completion). Anonymous reading mode. Custom tagging. Customizable via extensions. Less aggressively minimalist than Miniflux. |
| **Mobile / progressive web app** | PWA-capable (add to home screen, no app store required). Fully responsive. Touch gesture navigation optional. Works offline once cached. | Mobile web support (responsive, some features limited on mobile per docs). No PWA mention in official docs. Dependent on web server capabilities. |
| **Multi-user support** | Yes (built-in per official docs and framework references). User and category management. Per-user bookmarks and reading state. | Yes (built-in, multi-user from ground up). Anonymous reading mode available. Per-user tagging, reading state, bookmarks. User management interface built into admin panel. |
| **Authentication options** | Local username/password, WebAuthn (passkeys), OAuth2 (Google), OIDC, reverse-proxy auth. Modern and well-documented. | Web form (with optional anonymous mode), HTTP authentication (reverse-proxy compatible), OpenID Connect. Simpler than Miniflux but less modern (no WebAuthn/passkeys). |
| **Plugin / extension ecosystem** | No plugin system. 25+ integrations (Discord, Telegram, Slack, Notion, Readwise, Wallabag, Pinboard, Instapaper, Matrix, Linkding, Ntfy, Shaarli, Shiori, etc.). Webhooks enable custom integrations. | Extension framework with dedicated GitHub repo (FreshRSS/Extensions). Active extension ecosystem (exact count not verified, but documented as "further tuning"). Extensibility by design; community-authored. |
| **Maintenance / release cadence** | Very active. Recent releases: 2.2.19 (2026-04-05), 2.2.18 (2026-03-15), 2.2.17 (2026-02-13). Approximately one release per 2–4 weeks. Single maintainer (Frédéric Guillot) with responsive GitHub issue tracker. | Active. Recent releases: 1.28.1 (2026-01-25), 1.28.0 (2025-12-24), 1.27.1 (2025-09-27). Releases every 2–3 months per docs ("new versions every two to three months"). Community-driven. |
| **Configuration as code (env vars / config file)** | Environment variables (12-factor app methodology). Single config entry point via env vars or CLI flags. Stateless binary design. | PHP config file (config.default.php, overridable in data/config.php). Web-based setup wizard available. Configuration approach is traditional PHP (file-based, not env-based). |
| **Container image / deployment story** | First-class. Official Docker images on Docker Hub, GitHub Registry, Quay.io. ARM and RISC-V architecture support. Systemd sd_notify protocol support. Automated HTTPS with Let's Encrypt. Single image, straightforward deployment. | Well-supported. Docker available (official Docker directory in repo). Also supported on YunoHost, Cloudron, Elestio, PikaPods, Zeabur, Hostinger, ClawCloud (multiple PaaS options). More deployment flexibility via multiple platforms. |
| **Backup / restore mechanics** | Implicit: PostgreSQL backup/restore of entire database. Built-in export via Miniflux client/API. OPML export supported (for feed list). Full database persistence in PostgreSQL. | Explicit data directory model: all user data in `./data/` folder (SQLite/MySQL/PostgreSQL backend files, user logs, config). OPML export/import supported. Straightforward file-based backup of `./data/`. |
| **Integration friction with Python fetcher (substrate-locked path)** | Excellent. Official Python client library (`python-client` repo). REST API is first-class, well-documented. Deterministic API contracts. | Good. Google Reader API accessible via Python libraries (e.g., `grapi`). No native Python client; one HTTP layer away via API. Slightly more integration friction than Miniflux's native library, but workable. |

## Recommendation

**Confirm Miniflux as the default aggregator for both D-17-136 and D-17-137.**

The substrate doctrine's "Miniflux preferred default" stands on evidence:

1. **Operational simplicity:** Single Go binary eliminates the web server + PHP runtime dependency layer that FreshRSS requires. Easier to deploy in a containerized or minimal VM context, especially on the Mac Mini Pro orchestration node.

2. **Footprint advantage:** Miniflux's stated 2–5 MB RAM footprint vs FreshRSS's Raspberry Pi 1 performance (higher estimated cost) matters on a shared workstation. Every MB of idle memory on Mac Studio inference worker impacts available model context.

3. **Python integration:** Miniflux's native Python client and REST API are first-class design choices, not retrofits. D-17-136 and D-17-137's locked "Python fetch/export job" path is architecturally cleaner with Miniflux.

4. **Database commitment:** Miniflux's PostgreSQL-only choice forces discipline (one backend, no "config creep"). FreshRSS's flexibility (SQLite/MySQL/MariaDB options) is not needed for the RSS substrate; it creates unnecessary decision surface. This repo's initial advice is "SQLite first, promote on evidence" — Miniflux's opinionated PostgreSQL design aligns with the scaled-up (D-17-37) storage model more naturally.

5. **Release frequency:** Miniflux's 2–4 week cadence vs FreshRSS's 2–3 month cycle. For a system touching technical intelligence and personal briefing, more frequent security/stability updates matter.

The doctrine's acknowledgment of FreshRSS as "strong alternative (if UI/extensions matter)" remains valid; see "Override conditions" below.

## Override Conditions

The operator would legitimately choose FreshRSS over Miniflux in these scenarios:

- **Extension ecosystem priority:** FreshRSS's plugin architecture and active extension community outweigh Miniflux's integration webhooks, and custom processing is valuable enough to justify the Python fetcher consuming Google Reader API instead of native REST API.

- **Database flexibility:** Starting with SQLite and delaying PostgreSQL migration is preferred to Miniflux's hard PostgreSQL requirement.

- **Web server already present:** If the Mac Mini Pro or similar orchestration node already runs a web server (Apache/nginx for other services), FreshRSS's PHP footprint becomes marginal; the integration cost drops.

- **Multi-user UI importance:** FreshRSS's polished multi-user admin interface and anonymous mode are superior to Miniflux's simpler multi-user model (where available), and this UI priority outweighs Miniflux's operational advantages.

- **Instant push notifications (WebSub):** If trusted feed sources support WebSub (WordPress, Friendica, Blogger, Medium), FreshRSS's native WebSub support eliminates polling overhead. Miniflux has no WebSub support.

- **PaaS deployment preferred:** If the substrate shifts to managed hosting (YunoHost, Cloudron, etc.), FreshRSS's broader PaaS support ecosystem simplifies operations.

None of these overrides apply to the current D-17-136 / D-17-137 substrate model (self-hosted, Python fetcher, Mac Studio/Mac Mini Pro platform, no PaaS). The default remains Miniflux.

## Cross-references

- `docs/architecture-facts/rss-intelligence-substrate-doctrine.md` — substrate doctrine (parent)
- `docs/PROJECT_FRAMEWORK.md` D-17-136 — Technical Intelligence RSS
- `docs/PROJECT_FRAMEWORK.md` D-17-137 — Personal Briefing Engine
- D-17-37 — artifact storage substrate (QNAP)
- D-17-39 — roadmap ingestion flow
- Master log Section 16 (RSS intelligence ingestion) — verdict: PURSUE bounded
- Master log Section 17 (Roca-style Personal Briefing Engine) — verdict: PURSUE
- Official Miniflux docs: https://miniflux.app/docs/
- Official FreshRSS docs: https://freshrss.github.io/FreshRSS/en/
- Miniflux GitHub: https://github.com/miniflux/v2
- FreshRSS GitHub: https://github.com/FreshRSS/FreshRSS
