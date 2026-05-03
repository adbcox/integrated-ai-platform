# D-17-36 WP-05 — Sonarr Formula 1 disposition inventory
**Date:** 2026-05-03
**Scope:** Resolve deferred Sonarr workaround cleanup for series id=185.

## Sonarr-side state (series id=185)

| field                | value                                          |
|----------------------|------------------------------------------------|
| title                | Formula 1                                      |
| tvdbId               | 387219                                         |
| seriesType           | standard (TV — wrong fit, see retirement doc) |
| status               | continuing                                     |
| added                | 2026-03-15 (workaround for broken Sportarr)   |
| path                 | `/data/media/tv/Formula 1`                     |
| rootFolderPath       | `/data/media/tv`                               |
| qualityProfileId     | 1 (Any)                                        |
| monitored (series)   | true                                           |
| episodeCount         | 9                                              |
| episodeFileCount     | 5                                              |
| totalEpisodeCount    | 2486 (full TVDB metadata, not relevant)        |
| sizeOnDisk (Sonarr)  | 13,077,707,327 bytes = **12.18 GiB**           |

### Season distribution

Only one season has any monitored / file state. All others (s1950 → s2025) are
unmonitored with zero files registered:

| season | monitored | episodes | files | size       |
|--------|-----------|----------|-------|------------|
| s2026  | true      | 9 / 119  | 5     | 12.18 GiB  |
| s1950 → s2025 (76 seasons) | false | 0 | 0 | 0 |

### Episode files (s2026)

| s.e        | size     | added       | filename (release group)                                      |
|------------|----------|-------------|---------------------------------------------------------------|
| s2026e13   | 3.31 GiB | 2026-05-02  | Formula1 S2026E13 Australia Qualifying 1080p ANTP-playWEB     |
| s2026e14   | 2.58 GiB | 2026-05-02  | Formula1 S2026E14 Australia Race 720p ANTP-playWEB            |
| s2026e17   | 1.76 GiB | 2026-03-17  | Formula1 S2026E17 China Sprint Race 1080p ANTP-playWEB        |
| s2026e18   | 2.60 GiB | 2026-03-17  | Formula1 S2026E18 China Qualifying 1080p ANTP-playWEB         |
| s2026e19   | 1.94 GiB | 2026-05-02  | Formula1 S2026E19 China Race 1080p ANTP-playWEB               |

(Note: The retirement record cited 13.08 GiB on 2026-05-03 inspection; the
12.18 GiB above is from current Sonarr stats — diff is rounding / the retirement
record probably summed `du`'s extended count, see SMB note below.)

## Filesystem-side state

```
/data/media/tv/Formula 1
└── Season 2026
    ├── Formula1 S2026E13 Australia Qualifying ...      3.4G
    ├── Formula1 S2026E14 Australia Race ...            2.6G
    ├── Formula1 S2026E17 China Sprint Race ...         1.8G
    ├── Formula1 S2026E18 China Qualifying ...          2.6G
    ├── Formula1 S2026E19 China Race ...                2.0G
    ├── .smbdeleteAAAaabb4.4                            3.4G  ← SMB delete-pending
    ├── .smbdeleteBAAaabb4.4                            2.6G  ← SMB delete-pending
    └── .smbdeleteCAAaabb4.4                            5.9G  ← SMB delete-pending
                                                        ─────
                                                        24G   (du total)
```

**SMB delete-pending artifacts.** The 3 `.smbdelete*` files (~12 GiB) are
QNAP SMB-protocol artifacts from earlier in-progress deletes (likely client-
side renames during a copy or replace operation). They're not Sonarr-tracked;
they will be reaped by QNAP background SMB cleanup or on next reboot. They
inflate `du` from 12 GiB (real episode content) to 24 GiB. They are NOT part
of any disposition decision — they go away regardless.

## Plex-side state (TV library, key=2)

```
ratingKey=35192  type=show  title="Formula 1"  year=1950
  leafCount=5  viewedLeafCount=0
```

Per-episode breakdown (all 5 episodes):

```
s2026e13 → s2026e19   viewCount=0   viewOffset=0   (no playback ever; not even partial)
```

**Dispositive: zero watch state on every Sonarr-imported F1 file.** No
on-deck position, no view count, no partial-progress markers. Per the
prompt's WP-2 recommendation logic, this activates the **DELETE branch**
(option a).

## Sportarr canonical-path overlap check

Sportarr writes to `/data/media/sports/Formula 1/`. Current state:

```
/data/media/sports/Formula 1/
└── Season 2026/
    ├── Formula1.2026.Miami.Grand.Prix.Qualifying.1080p.AHDTV.x264-DARKSPORT.mkv  (7.4 GiB)
    └── Formula1.2026.Miami.Grand.Prix.Sprint.Race.1080p.AHDTV.x264-DARKSPORT.mkv (6.0 GiB)
```

**Zero overlap with Sonarr's content.** Sonarr has Australia + China sessions
(playWEB releases). Sportarr has Miami sessions (DARKSPORT releases).
Different events, different release groups, different filename conventions.
The two sets are disjoint. No file would be lost in any disposition path.

## Audit context (from D-17-36 retirement record)

> The 55.6% completion rate over 7 weeks of Sonarr operation is the
> dispositive evidence that Sonarr is the wrong tool for sports content.
> Sonarr's TV-show parser does not match the F1 release naming conventions
> reliably (post-broadcast WEB-DL drops with session-specific tags); episodes
> register but releases never grab. This is exactly the capability gap
> Sportarr was built to fill.

Sportarr is now `(healthy)` post D-17-36 close, with 1390 releases fetched
from 8 RSS feeds and a working release-parser. F1 going forward is owned by
Sportarr; the Sonarr workaround is no longer needed for *any* purpose.

## Disposition decision matrix

| option       | files            | Sonarr DB    | Plex impact            | recovery                 | recommendation |
|--------------|------------------|--------------|------------------------|--------------------------|----------------|
| (a) DELETE   | unlink 5 mkv     | DELETE series id=185 + drop history | TV library re-scan removes ratingKey=35192 (no playback impact: viewedLeafCount=0) | re-grab via Sportarr if ever wanted | **RECOMMENDED** |
| (b) ARCHIVE  | rsync to QNAP `/share/CACHEDEV2_DATA/_archive/sonarr-f1-2026-05-03/`, then unlink | DELETE series id=185 | same Plex outcome as (a) | restore from archive ≤90 days | over-engineered for zero-watch-state content |
| (c) MOVE     | rename into `/data/media/sports/Formula 1/Season 2026/`; attempt Sportarr DB relink | DELETE series id=185 | TV library loses entry, Sports library gains 5 entries (assuming Sportarr release-parser matches the playWEB filename convention) | irreversible; release-parser may misclassify (F12 territory) | rejected — playWEB filenames don't match DARKSPORT canonical pattern Sportarr is tuned for; high mis-import risk per Finding 7 |

### Why DELETE wins

1. **Zero watch state** — no playback, no progress markers, no on-deck
   position. Operator never engaged with Sonarr-imported F1 episodes.
2. **Zero overlap with canonical Sportarr content** — Australia + China
   playWEB releases don't compete with Miami DARKSPORT releases.
3. **Sportarr now functional** — going forward, F1 is owned by Sportarr's
   working release-parser. The workaround basis no longer holds.
4. **ARCHIVE adds storage cost without preserving any operator value**
   — there's nothing to preserve when nothing was ever watched.
5. **MOVE risks Finding 7 (F12) misclassification** — the playWEB
   release-name convention is not what Sportarr's release-parser is tuned
   for; we'd be importing 5 files into the wrong event records, then
   manually fixing them, then DELETE-ing anyway.

### What DELETE does in detail

1. Sonarr API `DELETE /api/v3/series/185?deleteFiles=true&addImportListExclusion=false`:
   - removes series from Sonarr DB (history, episodefile records, monitor state)
   - unlinks the 5 .mkv files in Season 2026/
   - removes the empty `/data/media/tv/Formula 1/` and `Season 2026/` dirs
2. Plex auto-rescan (or manual library scan trigger via API) drops
   ratingKey=35192 from TV library on next scan cycle.
3. SMB `.smbdelete*` artifacts are unaffected — they go away on QNAP's own
   schedule (out of scope).

### What DELETE does NOT do

- Does not touch Sportarr (no Sportarr DB rows reference these files).
- Does not touch the Sportarr canonical path `/data/media/sports/Formula 1/`.
- Does not touch any other Sonarr series (id=185 only).
- Does not modify Plex viewing history for any other library or show.
- Does not delete the series from TVDB / Sonarr's import-list — operator can
  re-add later if Sportarr ever becomes unsuitable.

## Surface back

**Recommendation: option (a) DELETE.**

Awaiting operator approval before executing. WP-3 surface-back per prompt
constraint ("DO NOT delete files without explicit approval").
