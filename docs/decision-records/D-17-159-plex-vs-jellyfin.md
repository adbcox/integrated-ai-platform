# D-17-159: Plex vs Jellyfin Decision

## Status

**ACCEPTED [B]** — Jellyfin migration path selected

**Decision date:** 2026-05-07 (flight session)  
**Decided by:** Operator (Adrian Cox)  
**Decided at:** GATE checkpoint, after reviewing ADR

---

## Operator decision (2026-05-07 flight session)

**Choice:** Option B (Jellyfin migration with Infuse on Apple TV)

**Reasoning:**
- Doctrine alignment with 100% OSS principle is non-negotiable
- Infuse on Apple TV mitigates UX gap (parallels Symfonium precedent: one paid client bridging OSS gap; server stays fully OSS)
- Plex vendor risk demonstrated historically; migration cost is bounded now vs unbounded later under forced conditions
- 30-day parallel run on QNAP is reversible and zero-incremental-cost
- Migration scope fits inside D-17-MEDIA window; doing it now avoids touching media stack twice

---

## Context

The home media stack currently runs **Plex** (closed-source server, proprietary apps, requires Plex.tv account for relay/remote access) as the primary streaming server on QNAP. With the media stack migration (D-17-MEDIA master plan) nearing completion, this is the right time to revisit the server choice against the operator's documented doctrine: **100% open-source self-hosted systems, with Proton cloud as the single exception**.

Plex is partially proprietary (server closed-source, apps closed-source, relay dependency). Jellyfin is fully open-source (server, apps, no cloud dependency). However, Plex offers polish and native app quality that Jellyfin does not yet match, particularly on Apple TV. Infuse is a paid, third-party client ($25/yr or $80 lifetime) that works with **both** Plex and Jellyfin, providing a bridge option.

This decision will shape the next 6–12 months of media consumption UX and operator philosophy enforcement. It is a good decision to make now, while migration effort is bounded and the library is organized (via D-17-155 TRaSH migration).

---

## Decision drivers (ranked by importance)

1. **Doctrine alignment** — operator stated: 100% OSS self-hosted; Symfonium (Android music app) is an accepted exception, but scope is narrow
2. **Daily-use polish** — native apps on iOS, macOS, Apple TV; streaming reliability; UI responsiveness
3. **Client flexibility** — device support (Apple TV, iOS, Android, web, QNAP native)
4. **Migration cost** — 30-day parallel run, library re-index, client setup on 5+ devices
5. **Feature parity** — library organization, search, recommendations, playback features
6. **Long-term support** — server updates, security patching, API stability

---

## Options

### Option A: Stay on Plex

**Rationale:** Plex is the "pay for polish" approach. Keep working system, avoid migration risk, get native app quality.

**Pros:**
- Native Plex app on Apple TV (highly polished, reliable, responsive)
- Native apps on iOS/macOS (App Store, mature, familiar UI)
- Android Plex app (also mature, works well)
- Zero migration effort; live library already organized
- Proven reliability over 2+ years (no downtime, steady updates)
- Web UI is polished and feature-complete
- Remote access works out-of-the-box (Plex relay handles NAT traversal)
- Symfonium precedent: already accepting proprietary apps where OSS is weak

**Cons:**
- **Doctrine deviation:** Plex is proprietary (server, apps, relay). Not aligned with 100% OSS mandate
- Plex.tv account required for remote access (cloud dependency)
- Relay adds latency and privacy tradeoff vs direct connection
- Monthly cost: Plex Pass (if desired) ~$5/mo; not required but unlocks features
- Closed-source means no control over roadmap or security issues
- Vendor lock-in: if Plex changes terms, operator is stuck
- Proprietary apps cannot be audited or modified

**Doctrine deviation plan:**
- Accept Plex as proprietary exception #2, alongside Symfonium
- Document rationale: "Plex = paid exception for streaming UX; Symfonium = paid exception for music UX; both fill gaps where OSS is not production-ready"
- Update master log doctrine section to codify the exceptions

**Estimated effort:** 0 hours (no migration)

---

### Option B: Migrate to Jellyfin (fully OSS)

**Rationale:** Jellyfin is the "100% OSS" approach. Full control, no vendor lock-in, aligned with doctrine. Trade native app polish for alignment.

**Pros:**
- **Doctrine alignment:** Fully open-source server, open-source apps, no cloud dependency
- No monthly cost (free)
- No vendor lock-in; fork-friendly, community-driven
- Full API access; can build custom tools if needed
- Direct connection (no relay), lower latency, better privacy
- Infuse works with Jellyfin (same client as Option A, but using Jellyfin backend)
- Ecosystem growing rapidly (Swiftfin for Apple TV improving, Jellystat for stats, plugins expanding)
- Philosophy alignment: "if we're serious about OSS, we commit to it"

**Cons:**
- **Rough edges:** Jellyfin Apple TV app (Swiftfin) not yet parity with Plex native app
  - UI slower, missing features (subtitles, playback speed, search refinement)
  - Ongoing development but not production-ready for all users
- iOS Jellyfin app (Amphetamine/Infuse workaround needed for polish)
- Android Jellyfin app (Gelli for music, Jellyfin for video) less polished than Plex
- Migration effort: 30-day parallel run, library re-index (2–4 hours), client reconfiguration on 5+ devices, potential playback troubleshooting
- Loss of Plex Pass features if currently used (or migrate them post-deploy)
- Smaller community (vs Plex's wider user base)
- Some features require plugins vs built-in (e.g., automatic playback resumption, smart playlists)

**Client strategy:**
- **Recommended:** Use **Infuse** on Apple TV (same paid client, works with Jellyfin backend, maintains polish parity)
- This makes Option B viable: Infuse (proprietary but justified as single client, like Symfonium) + Jellyfin (OSS backend)
- Infuse license carries over from Plex (if already owned) or costs $25/yr or $80 lifetime
- iOS/macOS: can use Jellyfin app or Infuse (both work)
- Android: Jellyfin app or Infuse

**Estimated effort:** 2–4 hours setup + 30 days parallel + ~1 hour per device reconfiguration

---

### Option C: Dual-run (both Plex and Jellyfin, same library)

**Rationale:** Have both for a period. Use Jellyfin as audit/learning ground; fall back to Plex if issues arise. Deferring full commitment.

**Pros:**
- Zero downtime; can migrate clients one at a time
- Jellyfin can be tested with non-critical devices first (e.g., bedroom Roku)
- Plex stays live for critical clients (Apple TV, primary TV)
- Gives Jellyfin ecosystem time to mature while operator evaluates
- Doctrine gets a "pass" (dual-run is technically compliant: Jellyfin is available)
- Reversible: can shut down Jellyfin anytime

**Cons:**
- **Confusion:** Two servers, same library; user experience fragmentation
- **Maintenance burden:** Two instances to patch, monitor, backup
- **Ongoing cost:** Still paying Plex Pass or Plex infrastructure costs
- **Defers decision:** Doesn't resolve the doctrine question; pushes to later
- **Inertia:** Easy to get stuck in dual-run indefinitely (ratcheting complexity)
- **Duplicated effort:** Still need to reconfigure some clients for testing Jellyfin

**This option is viable only as a bridge:**
- Run for 30 days: Jellyfin in "learn mode" on secondary devices
- At end of 30 days: choose A or B, shut down the other
- Not a long-term solution

**Estimated effort:** 1–2 hours setup + 30 days passive testing + decision hour at end

---

## Recommendation

**The operator must choose between Option A or Option B. Option C is a delay tactic and not recommended as a final state.**

### If doctrine alignment is non-negotiable: **Choose Option B (Jellyfin)**

**Reasoning:**
- Jellyfin is mature enough for daily use (server is stable; apps are "rough but functional")
- Infuse on Apple TV bridges the UX gap (same paid client, so not a new vendor lock-in)
- Aligns with stated 100% OSS philosophy; Infuse becomes the justified exception (like Symfonium)
- Migration effort is 1-time cost; long-term gain is full control + no vendor risk
- Operator has the technical chops to troubleshoot Jellyfin and possibly contribute back

**Suggested implementation (if operator chooses B):**
- WP-159-02: Deploy Jellyfin on QNAP (Docker, point to TRaSH `/data/media/` paths)
- WP-159-03: 30-day parallel: Jellyfin on secondary devices (Roku, phones); Plex on primary (Apple TV, bedroom TV)
- WP-159-04: Configure Infuse on Apple TV to use Jellyfin backend (upgrade or buy new license if needed)
- WP-159-05: Cutover: move remaining clients to Jellyfin, retire Plex
- WP-159-06: Document final state and lessons learned

---

### If daily-use polish is non-negotiable: **Choose Option A (Plex)**

**Reasoning:**
- Native Plex app on Apple TV is genuinely better UX than Swiftfin (objectively faster, more features)
- Infuse would still add cost ($25/yr) on top of Plex, so the "bridge" approach costs more, not less
- Operator has already accepted Symfonium exception (closed-source Android music app); Plex is parallel exception
- Migration effort is zero; risk is zero
- Daily streaming happens 100+ times/month; UX quality matters for this frequency

**Suggested doctrine update (if operator chooses A):**
- Add section to `master-log.md`: **Proprietary app exceptions**
  - Symfonium (Android music): OSS alternative (Subsonic, Nextcloud Music) exists but UX not mature for daily use
  - Plex (streaming server): OSS alternative (Jellyfin) exists but UX gap on Apple TV is material; justified until Swiftfin reaches parity
  - Proton (email/cloud): not open-source but required for privacy; accepted exception at design time

---

## Consequences (per choice)

### If Option A (Plex):
- **What changes:** Doctrine explicitly accepts proprietary exceptions; operator codifies why
- **What stays the same:** Live library, apps, workflows, no migration work
- **Daily impact:** None (current state persists)
- **Risk:** Plex policy change, price increase, security issue could trigger forced re-evaluation

### If Option B (Jellyfin):
- **What changes:** Streaming server becomes OSS; requires Infuse on Apple TV ($25/yr); Plex removed after 30-day parallel
- **What stays the same:** Library (same paths), Tailscale access, QNAP location, TRaSH organization
- **Daily impact:** Slight UX change on Apple TV (Infuse instead of Plex app); potential playback quirks in first 2 weeks
- **Risk:** Jellyfin plugin ecosystem may not cover all features operator relies on (rare, but possible)
- **Upside:** Full control, no vendor risk, ideology wins

---

## Migration plan (Option B only)

If operator selects Jellyfin:

**D-17-159 WP-02 through WP-06 (dependent work, deferred to home session with Mac Studio):**

```yaml
WP-159-02: Deploy Jellyfin on QNAP
  - Download Jellyfin Docker image: docker pull jellyfin/jellyfin:latest
  - mkdir -p /share/Container/jellyfin/config /share/Container/jellyfin/cache
  - docker run -d --name jellyfin \
      -v /data/media:/media:ro \
      -v /share/Container/jellyfin/config:/config \
      -v /share/Container/jellyfin/cache:/cache \
      -p 8096:8096 \
      jellyfin/jellyfin
  - Access at http://QNAP-IP:8096; set up admin account
  - Add library: Media → Add Library → Movies, pointing to /media/movies/
  - Repeat for TV, Music, Books

WP-159-03: 30-day parallel run
  - Jellyfin runs in background; Plex stays as primary
  - Assign Jellyfin to test devices: Roku, one iOS phone, one Android phone
  - Plex remains on Apple TV (main living room)
  - Monitor: playback, search, performance, any missing features
  - After 30 days, note any show-stoppers vs "rough but acceptable"

WP-159-04: Infuse on Apple TV
  - Buy/upgrade Infuse license if not already owned ($25/yr or $80 lifetime)
  - Install Infuse from App Store on Apple TV
  - Add Jellyfin as library: Settings → Add Library → Jellyfin
  - Configure Jellyfin URL: http://QNAP-IP:8096
  - Test playback: TV episode, movie, music (if Jellyfin supports; may need gstreamer plugin)

WP-159-05: Cutover
  - Remove Plex from all devices
  - Reconfigure iOS/macOS: use Jellyfin app or Infuse (recommend Infuse for consistency)
  - Reconfigure Android: Jellyfin app for video, Gelli for music (if used)
  - Verify library fully indexed in Jellyfin (can take 1–4 hours depending on size)
  - Shut down Plex on QNAP (or leave for 7 days as emergency fallback)

WP-159-06: Document final state
  - Update this decision record: mark Status = ACCEPTED
  - Document client setup per device in docs/runbooks/jellyfin-stack.md
  - Add to Decisions log: final choice, rationale, lessons learned
  - Note any Jellyfin quirks or workarounds applied
```

---

## References

- **D-17-MEDIA-master-plan.md** — overall media stack migration plan
- **Master log §28** — operator's doctrine on open-source (see section "Philosophy: 100% OSS self-hosted")
- **Symfonium precedent** — Symfonium chosen as proprietary exception for Android music (master log §28, agents/serena docs)
- **Infuse for Apple TV** — cross-compatible streaming client, works with Plex or Jellyfin backend
- **TRaSH guides** — media organization standard used in this stack (D-17-155 references)
- **Jellyfin upstream** — https://jellyfin.org/ (check current Apple TV app status before deciding)
- **Swiftfin** — native Jellyfin Apple TV client; monitor progress at https://github.com/jellyfin/swiftfin

---

## Decision summary (for operator)

**Option A (Plex):**
- Status quo; zero migration effort
- Polished UX everywhere (native apps)
- Doctrine compromise: accept Plex as exception #2 (after Symfonium)

**Option B (Jellyfin):**
- 1-time migration effort (~4 hours setup + 30 days parallel)
- Rough UX on Apple TV (but Infuse mitigates)
- Doctrine win: full OSS stack except Infuse (single paid client, justified)

**Choose based on:**
- Is doctrine alignment critical? → B
- Is daily UX quality critical? → A
- Can accept both tradeoffs? → A for now; re-evaluate in 12 months when Swiftfin matures

---

**DECIDED: OPTION B (JELLYFIN)**

Operator selected on 2026-05-07 (flight session):
- [x] Option B (Jellyfin) — ACCEPTED [B], WP-159-01 DONE, WP-159-02 through WP-159-06 gated on Mac Mini reachability

Next: WP-159-02 (Jellyfin Docker deploy on QNAP) when Mac Studio reachable. 30-day parallel run scheduled after WP-155 (TRaSH paths) completes.
