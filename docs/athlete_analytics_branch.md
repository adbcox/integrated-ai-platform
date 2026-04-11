# Athlete Analytics & Coaching Branch Specification

This branch is a local-first endurance performance analytics and advisory surface. It ingests structured exercise/health data, enriches it with environment context, analyzes fatigue/readiness, and issues advisory weekly coaching summaries. It remains advisory-only, keeps human judgment central, and plugs into the existing platform without affecting core control-plane, business, media, or product-definition branches.

## 1. Branch role

- **What it is for:** Aggregating Garmin/Strava activity+health data, enriching it with weather and air-quality context, computing readiness/training-load metrics, and emitting weekly coaching advisories (TSS, HRV trends, discipline volumes, recovery status) tied to upcoming races or training phases.
- **What it is not for:** No live plan rewriting, no automation that pushes updates back to planning tools, no overriding core policy gates, no infrastructure control-plane decisions, and no medical diagnosis.
- **System fit:** It sits beside the core branches as a specialized analytics/advisory layer. It exposes runtime manifests/reports under `runtime/athlete_analytics_*` and shares review/advisory artifacts via the dashboard without altering existing governance. Cross-branch linkages (e.g., to hardware/product-definition) can surface via candidate/advisory artifacts but follow the same naming and read-only rules.

## 2. Source inputs

- **Strava activities:** Raw activity exports (GPX/TCX/JSON) with discipline, distance, elevation, moving time, normalized power/Q, HR data.
- **Garmin activity/health data:** Detailed training metrics (running dynamics, recovery minutes, sleep, HRV, training status) and health snapshots.
- **Weather inputs:** Historical/forecast weather around activity start times (temperature, humidity, wind, precipitation) ingested via local CSVs or cached APIs without runtime execution.
- **Air quality inputs:** AQI/PM2.5/ozone per activity location/time; store in normalized CSV or json files alongside weather.
- **Race calendar/training targets:** Manual race dates, target phases (base/build/peak/taper), goal metrics; stored in `runtime/athlete_analytics_race_calendar.json`.
- **Optional manual annotations:** Training notes, subjective readiness entries, coach overrides, stored under `athlete_sources/notes/`.

## 3. Core architectural layers

1. **Source ingestion:** Scripts pull Garmin/Strava exports plus weather/AQ datasets into `runtime/athlete_analytics_activity_ingest.json` and `runtime/athlete_analytics_weather.json`.
2. **Normalization:** Convert varying formats into canonical training records with normalized timestamps, discipline tags, durations, power/load proxies (TSS, TRIMP), heart-rate zones, and health metrics.
3. **Feature extraction:** Derive weekly/daily aggregates, discipline-specific volume, normalized power, HRV trends, recovery indicators (resting HR, HRV delta, sleep score), and environmental exposures.
4. **Fatigue/readiness analysis:** Compute training load balance (acute:chronic ratio), monotony, trend indicators, readiness score, and fatigue warnings with uncertainty estimates.
5. **Advisory planning outputs:** Generate weekly advisory summaries comparing workouts/loads to race timeline/training phase, recommending intensity/volume adjustments or recovery focus.
6. **Review/human judgment layer:** All advisories feed into a review queue (`runtime/athlete_analytics_advisory_review_queue.json`) where a human confirms or annotates confidence before adopting suggestions.

## 4. Provenance requirements

Every advisory output records:
- Source data window (dates of activities reviewed).
- Activity/health metrics used (IDs/timestamps, e.g., Garmin activity IDs).
- Environmental data (weather/AQ records with timestamps/locations).
- Model/heuristic version (script tag or commit hash included in advisory metadata).
- Generation timestamp and advisory author (branch/process name).

## 5. Artifact model

Suggested artifacts:
- `runtime/athlete_analytics_manifest.json`: athlete identity, data freshness, summary counts.
- `runtime/athlete_analytics_activity_ingest.json`: raw ingestion logs referencing source files.
- `runtime/athlete_analytics_normalized_training.json`: canonical training/activity records with normalized metrics.
- `runtime/athlete_analytics_weekly_analysis.json`: aggregated metrics by week with readiness/fatigue indicators.
- `runtime/athlete_analytics_advisory_report.json`: advisory text, recommended adjustments, confidence bands, relevant metrics.
- `runtime/athlete_analytics_advisory_review_queue.json`: queue items waiting for human judgment (each with review_item_id, status, review_reason, operator_note, created/updated timestamps).
- `runtime/athlete_analytics_advisory_review_summary.json`: counts (total/open/deferred/reviewed), reason rollups, latest update.
- Optional `runtime/athlete_analytics_race_plan.json`: phase timeline, target TSS, race-specific notes.

## 6. Branch pattern alignment

The branch reuses the platform’s pattern where it makes sense:
- **Manifest/review queue/summary:** Follows the same naming conventions (`runtime/<branch>_manifest.json`, `_review_queue.json`, `_review_summary.json`).
- **Status helper:** Provide `scripts/build_athlete_analytics_advisory_status.py` to refresh summary counts.
- **Dashboard summary/detail:** Expose overview counts and detail drill-downs without writes.
- **Diagnostics:** Provide `runtime/athlete_analytics_diagnostics.json` capturing ingestion anomalies or missing data.
- **Candidate/advisory artifact:** Treat weekly advisories as “candidate” suggestions requiring review, mapping to `runtime/athlete_analytics_advisory_report.json` plus review queue.

It does **not** change control-plane logic or pipeline conventions — it is strictly advisory/write-once; dashboards only read the artifacts.

## 7. Advisory model

- Recommendations are advisory only, never enforced. Each suggestion clearly states “Recommendation” vs “Confirmed Plan.”
- Provide confidence ranges and note when data is incomplete (e.g., missing HRV for two nights).
- No silent plan rewrites; the branch never pushes to master plan files or external services.
- Human judgment required before any adoption; review queue items must be marked “approved” before considered actionable.

## 8. Key metrics and features

Early priorities:
- Activity volume per discipline (swim/bike/run/strength) over the prior 7/28 days.
- Training Stress Score (TSS) or power-based load proxies; if power missing, infer from pace/HR.
- HRV/resting HR trends for fatigue detection.
- Fatigue/recovery markers such as acute:chronic load, monotony, and recovery minutes.
- Environmental exposures (heat stress from temperature, pollution spikes from AQI) per activity.
- Race countdown and training phase context (base/build/peak/taper).
- Plan adherence: compare actual load to target TSS/prescribed volume.

## 9. Dashboard/reporting model

- **Overview:** Weekly summary tile showing readiness score, TSS load, recovery flag, and next race countdown.
- **Detail drill-down:** Weekly analysis details, activity list, environmental context, and confidence statements.
- **Advisory report view:** Review queue/summaries with advisory text, confidence, supporting metrics, and provenance links.
- **Diagnostics tile:** Data freshness, ingestion gaps, missing HRV/environment inputs.

## 10. Branch boundaries

Stay away from:
- Medical diagnosis or prescribing medication/supplements.
- Automatic automation that publishes to Strava/Garmin.
- Making changes to `policy.yaml` or `runtime.yaml` defaults.
- Core infrastructure, control-plane orchestration logic, or home automation behaviors.
- Any system-level plan rewrites without explicit human approval.

## 11. Recommended implementation sequence

1. **Phase 1:** Finalize this branch spec + define artifact model and naming.
2. **Phase 2:** Build local ingestion scaffolding for Garmin/Strava/Weather/AQ raw files under `athlete_sources/` and create ingestion logs.
3. **Phase 3:** Implement normalization + feature extraction scripts, storing canonical records in `runtime/athlete_analytics_normalized_training.json`.
4. **Phase 4:** Produce `weekly_analysis` and advisory report artifacts plus review queue/summary (advisory requires review logic).
5. **Phase 5:** Integrate dashboard read-only surfaces to consume overview/detail/advisory artifacts; add diagnostics tile.
6. **Later:** Optional integrations (e.g., linking to hardware/product-definition once advisory proves stable, or future auto-assist actions after human review).

## 12. Drift-prevention guidance

- Anchor every artifact in `runtime/athlete_analytics_*` and document new names in `docs/system_cohesion.md` before use.
- Keep the branch advisory-only: no automation writes, no plan publishing, no infrastructure control changes.
- Treat review queue items as the sole path for turning suggestions into confirmed actions; human operators must annotate them before adoption.
- Coordinate dashboard additions with control-plane architects so the read-only surfaces remain consistent with other branches.
- Schedule periodic spec reviews to ensure the branch remains aligned with the broader milestone roadmap and does not expand into unrelated domains.
