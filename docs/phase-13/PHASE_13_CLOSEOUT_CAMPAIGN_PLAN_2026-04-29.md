# Phase 13 — Closeout Campaign Plan

**Date:** 2026-04-29
**Author:** session continuity (post-Block-4.C closeout, commit `78ab414`)
**Scope:** Plan-only. Block roster, dependency graph, increment proposal,
gate structure, prerequisites, risk register, parallelism plan, open
questions for operator. **No execution.**
**Calibration baseline:** Block 4.C estimated 8–12 h, actual ~12 h with
17 surfaced discoveries (Discoveries #1–17 in
`PHASE_13_BLOCK_4C_C2_DISCOVERIES_2026-04-29.md`). Discovery overhead
of roughly +50 % over a clean estimate is the norm for novel-pattern
work; mechanical-pattern application against a known canonical
recipe runs closer to clean estimate.

---

## 1. Executive summary

| | |
|---|---|
| Total blocks scoped | **15** (1 doctrine, 1 hardening, 7 sub-blocks 4.D–4.J, 2 health/fitness, 4 cross-cutting) |
| Total estimated effort | **64–110 hours** (low–high), with most-likely point estimate **~85 h** |
| Critical-path length | **5 blocks** (4.A → 4.C → 4.D → 4.E → 4.G), already 3-of-5 closed |
| Realistic calendar at typical operator availability | **~6–10 weeks** at one execution increment per week (12–18 h/wk peak; 1 wk slack between for review/decisions) |
| Recommended first increment | **Increment 1: Doctrine + Connector hardening** (Options A + B from `POST_BLOCK_4C_NEXT_OPTIONS.md`). Combined ~7–10 h. Doctrine first, connector hardening second within the same window. Rationale in §4. |

**Why not pick Block 4.D first.** 4.D introduces three new external
surfaces simultaneously (InvenTree itself, Mouser API, DigiKey API)
and requires operator-side prerequisites (API key registration) that
have not been done. Doctrine work has the highest decay rate (Block
4.C patterns are crisp now; in two weeks they require re-derivation)
and zero external prerequisites. Connector hardening is in the same
prerequisite-free window and is the platform's single highest-blast-
radius integration. Bundling them into one increment respects the
12–18 h target and produces a single coherent "platform stabilisation"
deliverable before opening new external surface.

---

## 2. Block roster

Status legend: ✅ closed · 🟢 open, ready · 🟡 open, blocked on prereq · 🔵 deferred / future

| ID | Title | Scope sentence | Effort (h) | Risk | Status |
|---|---|---|---|---|---|
| 4.A | Pre-merge reconciliation | Branch consolidation + doctrine refresh + registry drift fix. | — | — | ✅ closed (`bed7d26`) |
| 4.B | Foundation audit + state-anchoring | Inventory CMDB / roadmap / decisions / runtime-state surfaces; identify gaps. | — | — | ✅ closed |
| 4.C | NetBox CMDB authority | Migrate registry YAML→NetBox, prove byte-identical equivalence, deprecate YAML. | — | — | ✅ closed (`ff05159`) |
| **D-OP** | Operating-model doctrine | Codify Block 4.C patterns (IV&V loop, equivalence harness, fold-gates discipline, parallelism patterns) into ADRs + runbook. | 2–3 | cosmetic | 🟢 open |
| **D-CN** | Plane connector hardening | Audit + fix `framework/plane_connector.py` per Discoveries #10–#15 (rate-limit, error hierarchy, pagination, payload-key, first-batch verify, dry-run apply-path simulation). | 4–6 | recoverable | 🟢 open |
| 4.D | InvenTree + suppliers | Deploy InvenTree (Postgres + Redis + Vault Agent sidecars), Mouser & DigiKey supplier integrations, 129-component CSV import, NetBox cross-reference custom field. | 8–14 | recoverable | 🟡 prereq: Mouser/DigiKey API credentials, components CSV |
| 4.E | Cross-index service | Joins NetBox + InvenTree + Plane + ADRs + Vault paths into a single queryable view. | 6–10 | recoverable | 🟡 blocked by 4.D |
| 4.F | Bluetooth label maker | Print device/part labels from InvenTree records via BLE (lowest priority). | 4–8 | cosmetic | 🟡 blocked by 4.D, hardware-dependent |
| 4.G | Vision-recognition InvenTree plugin | Identify components from photos, suggest InvenTree match. | 6–10 | recoverable | 🟡 blocked by 4.D |
| 4.H | Upgrade-watcher service | Track upstream releases of pinned images/binaries; flag drift; suggest pin bumps with changelog. | 4–7 | recoverable | 🟢 open |
| 4.I | Receipt-ingestion service | Gmail-driven; Claude vision → InvenTree draft parts (uses `claude-pro` quota for vision; doctrine-tested). | 6–10 | recoverable | 🟡 blocked by 4.D, prereq: Gmail OAuth scope, vision-API decision |
| 4.J | Network discovery → NetBox | Active scan + passive observation feeding NetBox dcim/ipam objects. | 6–10 | recoverable (write-into-NetBox) | 🟢 open |
| **HF-1** | Oura Ring 4 integration | Local time-series store + ingest from Oura cloud API; AI-coach-ready data layer. | 5–8 | recoverable | 🟡 prereq: Oura OAuth client, SDK choice |
| **HF-2** | Garmin Fenix/Edge integration | Activity + biometrics ingestion via Garmin Connect (or Garmin SDK); same TS store as HF-1. | 5–8 | recoverable | 🟡 prereq: Garmin Connect OAuth or alternate auth |
| **CL** | Phase 13 closeout | Final regression probe `phase-13-final`, PHASE_13 closeout doc, tag `v13-final`, stand-down report. | 2–3 | cosmetic | 🟡 blocked by all of 4.D–4.J or explicit deferral |

**Total open scope:** 12 blocks (D-OP, D-CN, 4.D, 4.E, 4.F, 4.G, 4.H, 4.I, 4.J, HF-1, HF-2, CL) = **58–97 h** + closeout 2–3 h = **60–100 h**, point estimate ~80 h.

Notes:
- D-OP and D-CN are the renamed versions of Options A and B from
  `POST_BLOCK_4C_NEXT_OPTIONS.md`. They are both pre-existing open
  Phase 13 follow-ons, not new scope introduced by this plan.
- Effort ranges include a +50 % discovery buffer where the block
  introduces novel patterns (4.D, 4.E, 4.I, 4.J, HF-1, HF-2). Blocks
  that mainly mechanically apply Block 4.C canonical patterns
  (D-OP, D-CN, 4.H) get a smaller buffer.
- All ranges are calibrated against 4.C's 8–12 h estimate / ~12 h
  actual (with 17 discoveries) — i.e. the high end of the estimate
  is what 4.C actually took. Plan accordingly.

---

## 3. Dependency graph

ASCII rendering. `→` means hard dependency (must precede). `…>` means
soft dependency (benefits-from-but-not-required). `‖` means parallel-
safe. Already-closed blocks are bracketed.

```
                                             ┌──────── HF-1 (Oura) ───┐
                                             │                        │
[4.A ✅] → [4.B ✅] → [4.C ✅] ─┬─→ D-OP ────┼─→ HF-2 (Garmin) ──┐    │
                              │              │                    │    │
                              ├─→ D-CN ──────┤                    │    │
                              │              │                    │    │
                              ├─→ 4.D ──┬──→ 4.E ───┐             │    │
                              │         │            │             │    │
                              │         ├──→ 4.F ─┐  │             │    │
                              │         │          │ │             │    │
                              │         ├──→ 4.G ─┤  │             │    │
                              │         │          │ │             │    │
                              │         └──→ 4.I ─┤  │             │    │
                              │                    │ │             │    │
                              ├─→ 4.H ─────────────┤ │             │    │
                              │                    │ │             │    │
                              └─→ 4.J ─────────────┤ │             │    │
                                                   │ │             │    │
                                                   └─┴─────────────┴────┴─→ CL
```

**Critical path (longest chain of hard deps from current HEAD):**

```
[4.C ✅] → 4.D → 4.E → CL          (3 open blocks; 16–27 h)
```

Note that 4.E joins 4.D's data with NetBox/Plane/ADRs/Vault; it is
on the critical path because the cross-index needs InvenTree as a
data source. CL waits on **all** open blocks unless the operator
elects to defer some to a Phase 14 successor.

**Hard dependencies:**
- D-CN benefits from D-OP (the connector hardening should land *after*
  the doctrine register has the patterns it implements), but technically
  could go first. Treated as soft.
- 4.D requires only 4.C-closed (✅).
- 4.E, 4.F, 4.G, 4.I require 4.D (InvenTree must exist).
- 4.H, 4.J require only 4.C (no InvenTree dependency).
- HF-1 and HF-2 are completely independent of 4.D–4.J; they could in
  principle precede the entire 4.D arc. They are placed late because
  the operator stated 4.D arc is higher current priority.
- CL requires all of 4.D, 4.E, 4.H, 4.J at minimum. 4.F, 4.G, 4.I, HF-1,
  HF-2 are operator-deferral-eligible (CL closes Phase 13 on whatever
  is in scope at that point; deferred items roll into Phase 14).

**Soft dependencies:**
- 4.E ⟵ HF-1, HF-2 (cross-index gains a sources-tab for biometrics if
  HF blocks have shipped; otherwise the cross-index ships without that
  axis).
- 4.G ⟵ 4.I (vision plugin and receipt ingestion both need a vision
  pipeline; doing 4.I first establishes the vision-call pattern).
- 4.J ⟵ 4.D (network discovery feeding NetBox can find network gear
  whose physical components live in InvenTree; not required, but
  reduces NetBox/InvenTree manual reconciliation).

---

## 4. Increment proposal

Increments are sized to a single execution window of ~12–18 h. Each
delivers a coherent, gateable artifact.

### Increment 1 — Platform stabilisation *(recommended first)*

**Blocks:** D-OP + D-CN
**Effort:** 6–9 h (D-OP: 2–3 h; D-CN: 4–6 h)
**Reasoning:**

1. **Highest decay risk first.** Block 4.C patterns are one commit
   behind us; in two weeks they require re-derivation. D-OP captures
   them while they are fresh.
2. **No external prerequisites.** Operator does not need to register
   API keys, buy hardware, or schedule downtime. Blocks the operator
   only on review/approval, not on side-channel work.
3. **D-CN before any new write-heavy connector consumer.** The Plane
   connector is the single highest-blast-radius integration in the
   platform (Discovery #16 silently no-op'd 603 PATCHes against live
   issues). Hardening it before 4.D/4.E land new consumers is
   cheaper than doing it after 4.D drags additional consumers along.
4. **Combined produces a single coherent "platform stabilisation"
   deliverable.** Both ADRs/runbooks (D-OP) and connector hygiene
   (D-CN) are platform-internal. Closing them as one increment lets
   the operator start Increment 2 (4.D) on a hardened foundation.
5. **Total fits well under 12–18 h target with margin** for discovery
   overhead. If D-CN's apply-path integration test reveals something
   surprising in Plane, 6 h grows to 8 h and stays in the window.

**Exit criteria:**
- 3 ADRs merged (NetBox-as-CMDB, round-trip equivalence, staged-toggle
  pattern).
- DECISION_REGISTER and `migrate-source-of-truth.md` runbook in repo.
- All 6 connector hardening sub-items closed (Discovery #14 fix,
  apply-path integration test, rate-limit audit, error class hierarchy,
  pagination contract, first-batch verify helper).
- Regression probe `increment-1-final` PASS, no new FAIL/WARN.
- Closeout doc `PHASE_13_INCREMENT_1_CLOSEOUT_<date>.md`.

### Increment 2 — Block 4.D: InvenTree + supplier integrations

**Blocks:** 4.D
**Effort:** 8–14 h (likely top of range due to two new external APIs)
**Reasoning:** First "open new external surface" increment. Sized to
one window. Requires operator-side prereqs (Mouser + DigiKey API keys
in Vault, components CSV staged) before kickoff. See §6.

### Increment 3 — Cross-index + drift watchers

**Blocks:** 4.E + 4.H *(parallelisable in design, but execute
sequentially within the increment to reuse pattern)*
**Effort:** 10–17 h
**Reasoning:** With InvenTree live, 4.E and 4.H both *consume* CMDB
state, which is the natural pairing. 4.E joins NetBox + InvenTree +
Plane + ADRs + Vault paths into a queryable view; 4.H watches upstream
release feeds and flags pin drift, which the cross-index then surfaces
in the same UI.

### Increment 4 — Network discovery + receipt ingestion

**Blocks:** 4.J + 4.I
**Effort:** 12–20 h (ceiling exceeds window; operator may split into
two increments)
**Reasoning:** Both blocks introduce automated *write* paths into
authoritative stores (4.J writes to NetBox; 4.I writes draft parts to
InvenTree). Pairing them lets the operator assess the "automated
write" pattern once. **Recommend splitting into 4a (4.J) + 4b (4.I)
if both look long.**

### Increment 5 — Vision plugin + label maker

**Blocks:** 4.G + 4.F
**Effort:** 10–18 h
**Reasoning:** Both extend InvenTree. 4.G (vision recognition) is
high-leverage; 4.F (BLE label maker) is lowest-priority but small.
Pairing keeps 4.F from becoming a never-shipped tail block.

### Increment 6 — Health/fitness ingestion

**Blocks:** HF-1 + HF-2
**Effort:** 10–16 h
**Reasoning:** Two structurally similar integrations (cloud OAuth →
local time-series). Doing them as one increment shares the OAuth and
TS-store deployment work. Operator may invert the order based on which
device data is more urgent.

### Increment 7 — Phase 13 closeout (CL)

**Blocks:** CL
**Effort:** 2–3 h
**Reasoning:** Doc + regression probe + tag. Closes Phase 13.

**Total:** 7 increments. Increments 4 and 6 are operator-deferral-
candidates if the calendar tightens — they roll into Phase 14 if Phase
13 needs to close earlier.

---

## 5. Per-increment gate structure

The IV&V loop (audit → execution → validation → regression) is the
default. Folded gates are appropriate when the work is mechanical
application of an already-validated canonical pattern. Reasoning per
increment below.

### Increment 1 — Platform stabilisation

| Sub-block | Gate type | Reasoning |
|---|---|---|
| D-OP audit (read existing ADRs, decide structure) | **Folded** (audit only; no exec/validation) | Doctrine work has no executable artifact to validate against; review is the validation. |
| D-OP execution (write ADRs + runbook) | **Folded** (one IV&V step) | Mechanical pattern application: take 4.C's evidence package and translate it into ADR/runbook shape. |
| D-CN audit (Discoveries #10–#15 review) | **Full IV&V** | New surface (we have not audited the connector against these specific discoveries before). |
| D-CN execution (each sub-fix individually) | **Folded** per fix | Each fix is mechanical once the audit identifies the line; bundle the 6 sub-fixes into one execution stage with one regression at the end. |
| Increment 1 close | **Full regression** | Standard gate close. |

### Increment 2 — Block 4.D

| Sub-block | Gate type | Reasoning |
|---|---|---|
| 4.D.1 Pre-deploy (port-conflict check, Vault entries, AppRole, compose authoring) | **Full IV&V** | Novel deployment; canonical pattern but applied to a new surface. Block 4.C surfaced 17 discoveries on a deployment of this shape. |
| 4.D.2 Deploy + bootstrap | **Full IV&V** | Same reasoning. Healthcheck pattern, upstream-flow default, port-conflict pre-check all apply. |
| 4.D.3 CSV import | **Folded** | Mechanical bulk insert against one external surface (InvenTree's REST). One re-read validation suffices. |
| 4.D.4 Mouser integration | **Full IV&V** | First contact with Mouser API. Rate limits, auth, pagination all unknown. |
| 4.D.5 DigiKey integration | **Folded** | Pattern from 4.D.4 should apply mechanically. If it doesn't, escalate to full IV&V. |
| 4.D.6 NetBox cross-reference custom field | **Folded** | Same canonical pattern as Block 4.C C5.2 (NetBox custom field provisioning); mechanical. |
| Increment 2 close | **Full regression** | Standard. |

### Increment 3 — Cross-index + drift watchers

| Sub-block | Gate type | Reasoning |
|---|---|---|
| 4.E design (read schemas of NetBox, InvenTree, Plane, ADR markdown) | **Full IV&V** | Cross-index design must round-trip; equivalence-harness doctrine (Discovery #16) applies. |
| 4.E execution | **Full IV&V** | New service; new write-side. |
| 4.H design + execution | **Folded** (one IV&V step) | Watch service is mechanical (upstream feed → diff against pin → emit notification); pattern is well-understood. |
| Increment 3 close | **Full regression** | Standard. |

### Increment 4 — Network discovery + receipt ingestion

| Sub-block | Gate type | Reasoning |
|---|---|---|
| 4.J audit (network gear inventory; existing NetBox dcim shape) | **Full IV&V** | Writes to authoritative store; mistakes are recoverable but loud. |
| 4.J execution | **Full IV&V** | First automated write into NetBox dcim outside the C5.2 migration. |
| 4.I audit (Gmail OAuth, vision-API decision, draft-part schema) | **Full IV&V** | Brand-new pattern (operator-quota-bearing vision API call + automated draft into InvenTree). |
| 4.I execution | **Full IV&V** | Same. |
| Increment 4 close | **Full regression** | Standard. |

### Increment 5 — Vision plugin + label maker

| Sub-block | Gate type | Reasoning |
|---|---|---|
| 4.G | **Full IV&V** | First InvenTree plugin; sandbox + signature questions to settle. |
| 4.F | **Folded** | Small block; BLE printing is mechanical once the discovery scan works. |
| Increment 5 close | **Full regression** | Standard. |

### Increment 6 — Health/fitness ingestion

| Sub-block | Gate type | Reasoning |
|---|---|---|
| HF-1 audit (Oura SDK choice, OAuth, schema) | **Full IV&V** | New external surface, new TS store. |
| HF-1 execution | **Full IV&V** | First fitness data block. |
| HF-2 audit | **Folded** | Pattern from HF-1 should apply. |
| HF-2 execution | **Folded** | Mechanical re-application. |
| Increment 6 close | **Full regression** | Standard. |

### Increment 7 — Phase 13 closeout

| Sub-block | Gate type | Reasoning |
|---|---|---|
| CL | **Folded** (one full regression) | Closeout = regression probe + doc + tag. |

---

## 6. External prerequisites

Consolidated list grouped by "blocks before X" so operator can batch
the side-channel work. Each item is the operator's responsibility,
*not* something a planning or execution session can do unattended.

### Before Increment 2 (Block 4.D)

1. **Mouser API key** — register at mouser.com, generate API key, push
   to Vault path `secret/mouser/api#key`. Mouser's API has a 1000
   calls/day per key default; verify whether this fits 129-component
   import + ongoing query needs.
2. **DigiKey API credentials** — register at digikey.com, generate
   OAuth client ID + secret, push to Vault path `secret/digikey/api`
   with fields `client_id`, `client_secret`. DigiKey uses OAuth 2.0
   client-credentials flow; the implementation will negotiate access
   tokens at runtime.
3. **Components CSV staged** — `docs/inventory/components-2026-04.csv`
   with 129 entries does not currently exist (verified via `find`).
   Operator must produce the CSV (or commit existing source) before
   4.D.3 can execute.
4. **Decide whether `CMDB_SOURCE` default flips** to NetBox before or
   during 4.D (C6 follow-up #17). Recommendation: flip during
   Increment 1 closeout regression if the post-4.C operational period
   has been quiet (≥1 week with no incidents that would have demanded
   YAML fallback).

### Before Increment 4 (Block 4.I)

5. **Gmail OAuth scope** — operator must authorise a Gmail OAuth
   client with `gmail.readonly` (or narrower per-label scope). Push
   to Vault path `secret/gmail/oauth` with fields per Google's spec.
6. **Decision: vision API.** Block 4.I uses Claude vision via
   `claude-pro` quota by spec; operator must confirm this is
   acceptable (alternative: local Ollama vision-capable model,
   currently `llava:13b` not in fleet). Per LLM Access Doctrine,
   platform services must NEVER depend on Anthropic API access — so
   4.I is technically an exception (ingestion is operator-triggered,
   not service-driven, but the line is thin). **This needs explicit
   operator decision before scope is finalised.**

### Before Increment 5 (Block 4.F)

7. **Bluetooth label maker hardware purchased and accessible** to the
   Mac Mini (USB-BLE dongle if Mac Mini's onboard BT is reserved).
   Confirm model: most options (Brother, Niimbot, Phomemo) have
   distinct BLE protocols; pick one before the block opens.

### Before Increment 6 (Health/fitness)

8. **Oura OAuth client** — register a personal-access OAuth app with
   Oura. Push to Vault path `secret/oura/oauth`. Decide between Oura
   Cloud API (cleanest) vs reverse-engineered local protocol (faster
   but unsupported).
9. **Garmin Connect access** — Garmin does not publish a public OAuth
   API; usual paths are (a) `garminconnect` Python SDK (unofficial,
   periodically broken by Garmin), (b) FIT-file export from Garmin
   Connect Web → local processing, or (c) Garmin Health API (paid,
   commercial). Operator decides which path before HF-2 opens.
10. **Local time-series store choice** — VictoriaMetrics is already
    deployed; it would naturally host the biometric data unless
    operator wants a dedicated TSDB (TimescaleDB is also in-stack via
    Zabbix). Decision belongs to HF-1 audit.

### Before Increment 7 (CL — Phase 13 closeout)

11. **Decide which open blocks roll into Phase 14** if calendar pressure
    demands an early Phase 13 close. Candidates: 4.F, 4.G, 4.I, HF-1,
    HF-2. Cores (4.D, 4.E, 4.H, 4.J) are recommended in-Phase-13.

### Hardware-arrival gates (out-of-band)

- **Mac Studio M3 arrival** — currently future-block (CLAUDE.md: "future
  blocks beyond Block 3"). If it arrives mid-campaign, expect a
  topology rewrite (Mac Mini control plane → Mac Studio compute, or a
  split). This is **not** a Phase 13 block but it could disrupt any
  running increment. See risk register §7 R-7.
- **Linux Threadripper arrival** — same shape as Mac Studio.

---

## 7. Risk register — top 10

Risks in priority order. Each lists *probability × impact* (rough,
based on 4.C calibration), then mitigation.

### R-1 — Plane API rate-limit storms during write-heavy increments
**P×I:** high × high
Block 4.C burned ~150 spurious failures in C4.4 due to a 2× rate-budget
consumption (Discovery #15). Increments 3–6 all introduce new Plane
read consumers (cross-index, watchers, label management).
**Mitigation:** D-CN includes apply-path integration test against
Plane staging, plus first-batch-verify helper. Land D-CN in Increment 1
**before** any future write-heavy block. Document the per-endpoint
rate-limit findings (Block 4.B addendum) on every connector consumer.

### R-2 — InvenTree CSV import fails partway with no resume
**P×I:** medium × high
129-component bulk import is the largest single-shot data move in the
campaign. If InvenTree returns 500 partway, 4.D.3 needs idempotent
re-run.
**Mitigation:** 4.D.3 must use part-number as natural key (not InvenTree
internal ID), with a "skip if exists" path. First-batch verify pattern
applies (Discovery #15).

### R-3 — Round-trip equivalence drift between NetBox and InvenTree
**P×I:** medium × high
4.E joins NetBox + InvenTree. If an InvenTree part's NetBox cross-
reference custom field drifts (manually edited, schema-changed,
lost during InvenTree restore), the cross-index emits stale joins.
**Mitigation:** equivalence-harness doctrine (Discovery #16) — 4.E must
ship with a `--verify-roundtrip` mode that re-reads both sources,
diffs, and exits non-zero on drift. Wire into the regression probe.

### R-4 — Operator-side OAuth flows block execution
**P×I:** high × medium
HF-1, HF-2, 4.I all need OAuth grants that only the operator can
complete (browser-driven). Increment cannot start without them.
**Mitigation:** Each prerequisite-bearing block opens with an explicit
"operator action required" gate before any code is touched. Catalogue
of OAuth registrations in §6.

### R-5 — Mouser/DigiKey API rate limits hit during 129-component import
**P×I:** medium × medium
Mouser's default 1000/day fits 129 single-pass calls but not iterative
re-runs. DigiKey's rate limits are documented per-OAuth-client.
**Mitigation:** 4.D.3 must cache supplier responses to disk on first
fetch. Re-runs use cache until explicit refresh. Apply Discovery #10
rate-limit awareness inherited from D-CN.

### R-6 — Discovery #14 (`create_issue` builder bug) causes silent label-
drop on new Plane issue creation today
**P×I:** medium × medium
Discovery #16 documented that `create_issue` at line 360 builds
`payload["label_ids"] = label_ids` which is the same wrong key Plane
silently ignores. **Any new issue created via the connector since
that line landed has had its labels silently dropped.** This is live
breakage today, not a hypothetical future risk.
**Mitigation:** D-CN sub-item Discovery #14 fix is the first thing in
Increment 1's connector hardening. Audit `bin/sync_roadmap_to_plane.py`
for affected issues and decide whether a back-fill is needed.

### R-7 — Mac Studio M3 / Threadripper arrival mid-campaign
**P×I:** medium × high
Hardware arrival changes the deployment topology — Mac Mini may demote
to "operator workstation" with the new host taking on control-plane
duties. Any block in flight when this happens needs to be paused and
re-evaluated for portability flags.
**Mitigation:** Every block's compose stack must declare Mac-only
dependencies in CLAUDE.md as KNOWN-LIMITATION (already doctrine).
Operator should signal expected arrival window so the planner can
size increments around it. If arrival is during an increment, prefer
to finish-and-close the current increment before triggering the
topology rewrite as a separate Phase 14 block.

### R-8 — Doctrine drift (D-OP decays before being applied)
**P×I:** high × medium
If D-OP slips beyond ~2 weeks, the patterns from 4.C will require
re-derivation from the closeout/discovery docs, eroding the doctrine's
crispness.
**Mitigation:** Make Increment 1 the **first** increment. This is the
strongest argument for not picking 4.D first.

### R-9 — Connector-hardening test suite flake against live Plane
**P×I:** medium × medium
D-CN's apply-path integration test runs against Plane staging. Plane
CE on a single machine (this deployment) doesn't have a staging
project; the test must run against a label-prefixed test project on
the live workspace.
**Mitigation:** D-CN execution creates a `test-` prefix label set and
test issues at start, exercises the apply path, and tears down on
finally. If teardown fails, regression probe surfaces the litter.

### R-10 — Gmail receipt ingestion (4.I) double-creates parts
**P×I:** medium × high
If 4.I's email-watcher state drifts (last-processed-msg ID lost), it
re-processes recent receipts and creates duplicate draft parts in
InvenTree.
**Mitigation:** 4.I must use the email's Message-ID header as the
idempotency key on InvenTree's draft side; reject duplicates at
write-time, not at create-time. First-batch verify pattern applies
to the first day's haul.

### Bonus risks the operator may not have flagged

- **R-A — Vault `secret/anthropic/api` deletion (Phase 13.5 §6) pre-
  empts 4.I if 4.I lands first.** Phase 13.5's plan is to delete that
  path; 4.I uses Anthropic vision via `claude-pro` (not the platform
  Vault path), so this is technically fine, but the optics may
  surprise. Doctrine states platform services must not depend on
  Anthropic — so 4.I needs a clear "operator-triggered, not platform
  service" framing.
- **R-B — `~/control-center-stack/stacks/*` out-of-repo compose
  changes** are invisible to git. Every stateful deploy in the
  campaign must capture pre/post snapshots in the rewire log
  (CLAUDE.md doctrine). Easy to forget under time pressure.

---

## 8. Parallelism plan

Block 4.C surfaced parallelism patterns: read-only audits parallelise
aggressively, stateful deploys serialise carefully, and rate-limited
external APIs sequence to avoid contention. Applied to this campaign:

### Read-only audits — parallelise

- **D-OP** is doctrine-only; can run in parallel with **D-CN audit**.
  In practice the operator runs them sequentially within Increment 1
  for context coherence, but they could be split across two windows.
- Pre-execution audit stages of every block (C1-equivalent: read
  state, identify gaps) parallelise. The operator can audit 4.D, 4.E,
  4.H simultaneously if a planning session is the goal.

### Stateful deployments — serialise

- **4.D, 4.E, 4.G, 4.I** all touch InvenTree as a stateful
  authoritative store. Must serialise.
- **4.J** writes to NetBox. Must serialise against any other NetBox
  write (none scheduled in Phase 13 except C6 #17 default flip).
- **HF-1, HF-2** both write to whatever TS store HF-1 picks. Must
  serialise against each other but can parallelise against the 4.D
  arc.

### Rate-limited external APIs — sequence to avoid contention

- **Plane API** is consumed by D-CN, 4.E (cross-index), and the
  long-running roadmap sync. D-CN's apply-path integration test must
  not run while a roadmap sync is in flight. Sequence: D-CN's test
  windows are explicit, no other connector consumer runs during them.
- **Mouser API** (4.D) and **DigiKey API** (4.D) have separate
  per-key rate buckets. Can run in parallel within the import.
- **Anthropic vision API** (4.I, if chosen) is `claude-pro` quota.
  Must not run during a session where the operator also wants
  `claude-pro` orchestration. Sequence: 4.I runs in a dedicated window.
- **Oura, Garmin** APIs are independent. Can parallelise HF-1 and
  HF-2's API calls if the runs are simultaneous; in practice they will
  be sequential within Increment 6.

### Cross-increment parallelism (operator-decision)

If a second compute resource becomes available (e.g. Mac Studio M3
arrives mid-campaign), increments that share **no** stateful
dependencies can run in parallel:

- **Increment 4 (4.J + 4.I)** parallelises with **Increment 6 (HF-1 +
  HF-2)** — no shared stateful store.
- **Increment 5 (4.G + 4.F)** parallelises with **Increment 6** — same.
- **Increment 3 (4.E + 4.H)** does **not** parallelise with Increment 4
  (both read NetBox; 4.J writes NetBox; 4.E reads while 4.J writes
  creates a race).

In single-operator mode, increments execute sequentially.

---

## 9. Open questions for operator

These are decisions surfaced by the planning work that the operator
must answer before execution increment 1 can begin. Listed in
priority order — first three block Increment 1 directly.

### Q-1 — Increment 1 scope: is the D-OP + D-CN bundle correct?
**Why it matters:** This plan recommends bundling Options A + B from
`POST_BLOCK_4C_NEXT_OPTIONS.md` into one increment. The operator may
prefer them as separate increments (each ~2–6 h, two clean windows)
or may want to skip D-OP entirely (treat doctrine as captured-by-
closeout-docs and proceed to D-CN alone).
**Default if no answer:** bundle into Increment 1 as planned.

### Q-2 — Which Plane connector consumers are in scope for D-CN's audit?
**Why it matters:** Discovery #10's C6 follow-up names three known
consumers (`bin/sync_roadmap_to_plane.py`, `bin/sync_plane_to_markdown.py`,
`mcp/plane_mcp_server.py`). Verification this session shows actually
**six** consumers in `bin/`, `scripts/`, `mcp/`. D-CN should audit all
six. Operator confirmation.
**Default if no answer:** audit all six discovered consumers.

### Q-3 — Does the operator want to back-fill labels on
`bin/sync_roadmap_to_plane.py`-created issues?
**Why it matters:** R-6 above. The `create_issue` builder bug
(Discovery #14) means every issue created via the roadmap-sync since
the bug landed has had its labels silently dropped. Block 4.C C4
back-filled labels on **existing** issues from a different angle (Plane
prefix → label) — this would be its mirror (any roadmap-sync-created
issue → its declared labels). This may be already-covered by C4 or may
need a separate sweep.
**Default if no answer:** D-CN's audit reports the gap; operator
decides at audit close whether to schedule the back-fill in-Increment-1
or roll into a Phase 14 hygiene block.

### Q-4 — Increment 2 prerequisites: are Mouser + DigiKey credentials
achievable in operator's typical timeframe?
**Why it matters:** Both APIs require account registration, and Mouser
in particular may take 1–3 business days for key approval. Increment 2
cannot start until both are in Vault.
**Default if no answer:** Increment 1 executes; operator gets the
prereqs in flight in parallel; Increment 2 schedules when prereqs land.

### Q-5 — Components CSV: source and shape?
**Why it matters:** `docs/inventory/components-2026-04.csv` is named in
`POST_BLOCK_4C_NEXT_OPTIONS.md` but does not exist. 129 components
implies the operator has the inventory somewhere (spreadsheet, paper,
existing tool). Audit needs source and shape (CSV column schema,
manufacturer-part-number canonical or vendor-specific) before 4.D.3
can deploy.
**Default if no answer:** 4.D opens with an audit stage that asks the
operator to produce the CSV; if not ready, 4.D pauses there.

### Q-6 — `CMDB_SOURCE` default flip: when?
**Why it matters:** C6 follow-up #17. Recommendation: flip during
Increment 1 closeout if post-4.C operational period (currently 0 days)
has been quiet for ≥1 week. By the time Increment 1 typically lands
(operator-availability-dependent, ~3–7 days from today), the threshold
may be met or not.
**Default if no answer:** plan retains the flag default at `yaml`
through Increment 1 and re-evaluates at Increment 2 kickoff.

### Q-7 — Vision-API decision for 4.I
**Why it matters:** R-A. Per LLM Access Doctrine, platform services
must not depend on Anthropic. 4.I's vision call needs an explicit
exception (operator-triggered, not service-driven) **or** a local
fallback (`llava:13b` not currently in fleet — would need 4.I to add
it).
**Default if no answer:** 4.I's audit opens with this question;
execution does not start until answered.

### Q-8 — Which optional blocks roll into Phase 14?
**Why it matters:** If the calendar tightens, 4.F (label maker), 4.G
(vision plugin), 4.I (receipt ingestion), HF-1 + HF-2 (fitness) are
operator-deferral candidates. CL closes Phase 13 on whatever is in
scope at that point.
**Default if no answer:** all blocks remain in Phase 13; CL slides to
match.

### Q-9 — Hardware arrival timeline?
**Why it matters:** R-7. If the Mac Studio M3 or Linux Threadripper
arrives mid-campaign, the topology rewrite is a separate block (Phase
14 or interrupt-Phase-13).
**Default if no answer:** plan assumes single-host (Mac Mini)
through Phase 13 close.

### Q-10 — Garmin auth path?
**Why it matters:** R-4 / §6 prereq #9. `garminconnect` SDK is
unofficial and breaks periodically; FIT-file export is manual; Garmin
Health API is paid. Each has very different effort.
**Default if no answer:** HF-2 audit opens with this decision; HF-2
execution does not start until answered.

---

## Top 3 questions blocking Increment 1

The operator must answer these three before Increment 1 can begin
execution:

1. **Q-1 — Is the D-OP + D-CN bundle into Increment 1 acceptable?**
2. **Q-2 — Audit all six Plane connector consumers (or just the three
   in the C6 follow-up)?**
3. **Q-3 — Schedule the `create_issue` label back-fill in Increment 1,
   or defer to Phase 14?**

All other questions can be answered in parallel with Increment 1
execution and only block subsequent increments.

---

## Appendix A — Sources cited

- `CLAUDE.md` (project doctrine, post-Block-2 follow-up list, LLM
  access doctrine, known hardening trade-offs)
- `docs/phase-13/PHASE_13_BLOCK_4C_CLOSEOUT_2026-04-29.md`
- `docs/phase-13/POST_BLOCK_4C_NEXT_OPTIONS.md` (commit `78ab414`)
- `docs/phase-13/PHASE_13_BLOCK_4C_C2_DISCOVERIES_2026-04-29.md`
  (17 discoveries, all reviewed)
- `docs/phase-13/PHASE_13_BLOCK_4A_CLOSEOUT_2026-04-29.md`
- `docs/phase-13/PHASE_13_BLOCK_3_P7_CLOSEOUT_2026-04-29.md`
- `docs/phase-13/PHASE_13_BLOCK_2_CLOSING.md`
- `docs/phase-13/PHASE_13_BLOCK_2_5_CLOSING.md`
- `docs/phase-13/STATE_ANCHORING_DISCOVERY_2026-04-29.md`
- `docs/phase-13/h1-regression-probe.sh`
- `docs/adr/ADR-A-001` through `ADR-A-010` (10 ADRs, all reviewed)
- `framework/plane_connector.py` (525 lines, 6 consumers identified
  in `bin/`, `scripts/`, `mcp/`)
- `scripts/cmdb_source.py` (dual-backend loader)
- `config/service-registry.yaml.DEPRECATED` (header reviewed)
- `git log` (commits `78ab414`, `ff05159`, `ad614aa`, `f5742e1`,
  `d05d3bd`)

## Appendix B — Calibration notes

The 4.C estimate was 8–12 h. Actual was ~12 h with 17 discoveries
surfaced. Of those:
- 7 surfaced during C2 deployment (port-conflict, postgres breaking
  change, healthcheck PID-1, upstream-flow default, housekeeping path,
  partial-token print, SSH-noise on lsof) — novel-pattern discovery
  cluster.
- 4 surfaced during C4 backfill (token divergence, pagination non-
  termination, apply-path 2× rate, payload-key silent ignore) —
  connector-quality cluster, all in `framework/plane_connector.py`.
- 1 surfaced during C5.2a equivalence probe (lossy migration on three
  dimensions) — round-trip-equivalence cluster.
- 5 are roll-ups / cross-references / cleanup tasks.

The pattern: novel-pattern blocks (4.D as the closest analogue) should
expect a discovery cluster of 5–10. Mechanical-pattern blocks (HF-2
relative to HF-1, DigiKey relative to Mouser, 4.G's plugin relative
to existing InvenTree plugin pattern) should expect 1–3.

Effort estimates in §2 reflect this:
- Novel-pattern blocks: low end is "if no discoveries", high end is
  "with cluster of 5–10".
- Mechanical-pattern blocks: low end is "trivial", high end is "if
  the canonical pattern needs a small extension".

This is the calibration this plan asks the operator to accept. If
prior 4.A/4.B/4.C effort tracking shows a different pattern, the
operator should adjust before Increment 2 opens.

---

## Appendix C — Operator decisions on Q-1 / Q-2 / Q-3

**Date:** 2026-04-29
**Decided by:** operator, in response to the post-plan summary of
the top three Increment-1-blocking questions surfaced in §9.

These decisions resolve the three questions that blocked execution
of Increment 1. The body of this plan (§§1–9) was written before
these answers were given; it remains the canonical scope statement.
This appendix is the authoritative record of the operator's
disposition on the three blocking questions.

### Decision A-1 — Increment 1 scope (resolves Q-1)

**Decision:** Bundle D-OP and D-CN into a single Increment 1.

**Effect on plan:** §4 Increment 1 ("Platform stabilisation") stands
as written. Combined estimate 6–9 h (D-OP 2–3 h + D-CN 4–6 h),
single execution window, doctrine first then connector hardening.
Single Increment-1 closeout doc and regression probe at the end.

### Decision A-2 — D-CN audit scope (resolves Q-2)

**Decision:** Audit all six discovered Plane connector consumers,
not just the three named in C6 follow-up #10.

**The six consumers** (verified by `grep -rln "plane_connector"
bin scripts mcp framework` during planning research):

1. `bin/configure_plane_agile.py`
2. `bin/ai_requirement_translator.py`
3. `bin/sync_roadmap_to_plane.py` *(C6 #10 named)*
4. `bin/sync_plane_to_markdown.py` *(C6 #10 named)*
5. `scripts/backfill-plane-labels.py`
6. `mcp/plane_mcp_server.py` *(C6 #10 named)*

**Effect on plan:** D-CN's effort estimate in §2 (4–6 h) holds at
the upper end. The audit covers six consumers instead of three;
the per-consumer audit step is mechanical (read each consumer's
exception handling around `RateLimitError` and `Exception`, verify
pagination usage, verify payload-key correctness on any write
calls, document findings) and the six fit comfortably inside the
existing window. No re-sizing of Increment 1.

### Decision A-3 — `create_issue` label back-fill scheduling (resolves Q-3)

**Decision:** Schedule the `create_issue` label back-fill inside
Increment 1, executed **immediately after** the connector
hardening work (D-CN) and **before** the Increment 1 closeout
regression probe.

**Why this ordering matters:**

1. The fix to `framework/plane_connector.py:360`
   (Discovery #14 — `payload["label_ids"]` → `payload["labels"]`)
   is part of D-CN. Running the back-fill *before* D-CN would
   re-trigger the same silent-no-op failure that motivated the
   back-fill (Discovery #16 echoes this — wrong key, HTTP 200,
   zero mutation).
2. Running the back-fill *after* the D-CN fix lands but *before*
   the Increment 1 closeout regression means the regression probe
   sees a Plane state that reflects both the doctrine update (D-OP)
   and the consumer correction (D-CN + back-fill) as a single
   coherent post-Increment-1 state.

**Scope of the back-fill:**

- Identify Plane issues created via `bin/sync_roadmap_to_plane.py`
  since the `create_issue` line landed (Plane creation timestamp
  + roadmap-sync-shaped issue identifier are the joinable signals).
- For each affected issue, recompute the labels the roadmap source
  declared and apply them via the corrected `update_issue` PATCH
  path (now using `payload["labels"]` per Discovery #16's fix to
  `scripts/backfill-plane-labels.py`).
- Apply the first-batch-verify pattern (Discovery #15) — re-GET
  the first issue after PATCH and confirm the labels landed before
  sustaining the run.
- Idempotent on re-run: if an issue already has the target labels,
  skip (matches the existing C4 backfill skip-already-labeled path).

**Increment 1 effort revision:**

| Sub-block | Estimate (h) |
|---|---|
| D-OP — operating-model doctrine | 2–3 |
| D-CN — Plane connector hardening (six consumers, all six C6 sub-items) | 4–6 |
| **Back-fill (newly folded in)** | **1–2** |
| Increment 1 closeout (regression probe + closeout doc) | 0.5 |
| **Total Increment 1** | **7.5–11.5 h** |

The back-fill add is scoped at 1–2 h because:
- The infrastructure already exists (`scripts/backfill-plane-labels.py`
  is the C4 vehicle and was patched in C5.x to use the correct
  `payload["labels"]` key per Discovery #16).
- The work is "identify the affected subset of the 604 issues and
  re-run a known-good script over that subset" — mechanical pattern
  application, not novel work.
- The risk path (R-1 rate-limit storm, R-6 silent no-op) is
  pre-mitigated by D-CN landing first within the same increment.

**Increment 1 still fits the 12–18 h target window** with margin.

### Updated Increment 1 sequence (post-decisions)

1. **D-OP** — write 3 ADRs (NetBox-as-CMDB, round-trip equivalence,
   staged-toggle pattern), update DECISION_REGISTER, write
   `docs/runbooks/migrate-source-of-truth.md`.
2. **D-CN audit** — read all six consumers, produce a findings
   table.
3. **D-CN execution** — apply the six C6 sub-items
   (Discovery #14 fix, apply-path integration test, rate-limit
   audit closure, error class hierarchy, pagination contract,
   first-batch verify helper) plus any consumer-specific fixes
   surfaced by the six-way audit.
4. **`create_issue` label back-fill** — identify affected
   issues, run the corrected back-fill script, sample-verify.
5. **Increment 1 closeout** — regression probe
   `increment-1-final`, closeout doc, commit.

### What did NOT change

- The §2 block roster (12 open blocks).
- The §3 dependency graph.
- The §4 increment proposal for Increments 2–7.
- The §5 gate-structure recommendations.
- The §6 external-prerequisites catalogue.
- The §7 risk register (R-1, R-6 mitigations are already aligned
  with this decision; the back-fill landing inside Increment 1 in
  fact *strengthens* R-6's mitigation by closing the breakage
  same-window).
- The §8 parallelism plan.
- The §9 questions Q-4 through Q-10 (still open, not blocking
  Increment 1).

The plan is now execution-ready for Increment 1.
