# System Milestone Roadmap

This milestone roadmap builds on the governance scaffolding in `docs/system_cohesion.md`. It turns the current architecture state into a concise, staged execution plan designed to keep every branch aligned, minimize drift, and give operators a clear, conservative progression path.

## 1. Current system state

- **Control-plane / infrastructure** – Core orchestrator is in place with the dashboard, `summary`/`capabilities` reporting, policy enforcement, and live-state comparison helpers. It is foundationally complete but still needs tighter guardrails for new branch integrations.
- **Home Assistant appliance role** – Treated as a stable appliance surface. Its runtime hooks and status feeds exist, and no deeper development is needed beyond occasional maintenance updates.
- **Knowledge / reconciliation** – The manifest and review scaffolds exist conceptually, but they remain mostly at scaffolding maturity (few automated reviews or linkages).
- **Media** – Ingesters, manifests, and review queues are running; this branch is broadly feature-complete for its original scope.
- **3D assets** – Manifests and review queues exist; the branch is now co-managing the hardware linkage scaffolds and is integration ready.
- **Hardware / product-definition** – Manifests, diagnostics, candidate scaffolds, and review artifacts are present; hardware is ready for integration work under governance rules.
- **Cross-branch linkage scaffolds** – Hardware↔3D and hardware↔reconciliation scaffolds (candidates, diagnostics, queue, summary, detail surfaces) are live. They now form the first two governed cross-branch patterns and prove the read-only workflow for future link efforts.

## 2. Architecture guardrails

- **Use the shared runtime naming** (`runtime/<branch>_manifest.json`, `_review_queue.json`, `_review_summary.json`, `_link_candidates.json`, `_link_diagnostics.json`). Never deviate without updating `docs/system_cohesion.md` first.
- **Keep dashboards read-only** – All branch detail and cross-link surfaces must render from `runtime/` artifacts. No template should trigger writes or policy changes.
- **Review items are canonical** – Each queue entry must include `review_item_id`, `source_path`, status, `review_reason`, `operator_note`, and timestamps; cross-branch scaffolds must reuse this exact structure.
- **Policy gates stay central** – No branch modifies `policy.yaml` or `runtime.yaml` defaults. Any gate updates funnel through control-plane tooling, not branch helpers.
- **Integrations follow the pattern** – New candidate/diagnostic/review artifacts must align with the scaffold conventions so the dashboard and future automation can treat them uniformly.

## 3. Major milestones

1. **Foundational manifest & review stabilization**
   - *Purpose*: Ensure every branch has a deterministic manifest, review queue, and summary before new data surfaces are added.
   - *Why it matters*: Foundations enable predictable dashboards and prevent data loss once linkages accumulate.
   - *Done looks like*: Each branch enumerated in `docs/system_cohesion.md` produces canonical `runtime/` manifests, review queues, and summaries plus corresponding ingest scripts.

2. **Governed cross-branch linkage review completion**
   - *Purpose*: Wrap hardware↔3D with a full evidence chain (candidates, diagnostics, review queue/summary, dashboard overview, drill-down) before adding new link paths.
   - *Why it matters*: Operators get a trusted workflow for triaging matches before any writes occur, reducing future remediation.
   - *Done looks like*: Dashboard surfaces the linkage queue/summary, diagnostics explain misses, and review status helper keeps counts in sync.

3. **Reconciliation decision-usefulness**
   - *Purpose*: Turn the matured hardware↔reconciliation scaffolds into genuinely decision-useful tools by hardening the normalization, grouping/conflict scaffolding, candidate usefulness, and review maturity.
   - *Why it matters*: BOM truth and product-definition reviews depend on reconciliation confidence; improving normalization and review signals keeps linkage recommendations conservative and manual-review safe.
   - *Done looks like*: Candidate/diagnostic/review artifacts remain live, the hardware detail view exposes their status, and reconciliation normalization plus conflict-scaffolding scripts supply clearer candidate ranks without triggering automated writes.

4. **Governance-ready integration pipeline**
   - *Purpose*: Harden the control-plane scripts so future cross-branch linkages can plug into the same status helpers, dashboards, and policy checks.
   - *Why it matters*: Avoids ad-hoc patterns and keeps every integration reusing the same naming and read-only enforcement logic.
   - *Done looks like*: Control-plane scripts reference shared constants, dashboards automatically pick up new link summary artifacts, and no new branch bypasses the guardrails.

## 4. Recommended sequencing

- **What should be done next**: Make the knowledge/reconciliation branch more decision-useful by maturing normalization, grouping/conflict scaffolding, candidate/recommendation usefulness, and review workflow maturity, leveraging the existing hardware↔reconciliation artifacts. Hardware-linkage UI depth is now secondary and should remain stable while these signals improve.
- **What should wait**: Live remediation/action automation (e.g., action-plan scripts targeting reconciliation/BOM) and any Home Assistant expansions outside stability fixes.
- **What should not be widened yet**: Avoid introducing new branch-to-branch candidates (e.g., hardware↔firmware) until both sides have stable manifests and the cross-branch review template proven with hardware↔3D and hardware↔reconciliation.

## 5. Branch-by-branch priority guidance

- **Control-plane** – Keep the orchestrator stable, shepherd new review artifacts into the dashboard, and ensure any status helpers reference the canonical naming patterns. Focus next on wiring reconciliation review summaries into the overview tile.
- **Home Assistant** – Maintain its appliance runtime surfaces; treat it as a read-only dependency during this roadmap cycle (no new branches should deepen here).
- **Knowledge / reconciliation** – The branch now has canonical manifests, candidates, diagnostics, and review queues; the priority is to improve normalization maturity, grouping/conflict scaffolding, candidate ranking clarity, and the review helper so reconciliation becomes decision-useful without introducing writes.
- **Knowledge / reconciliation future enrichment (later/advisory)** – Consider document-style clustering, section-level writing-tone grouping, and authorship-similarity signals as optional advisory enhancements. These low-confidence cues must remain manual-review oriented, explicitly advisory (no identity truth claims), and must never block the core reconciliation maturity work.
- **Media** – Continue monitoring existing manifests and review queues. Only revisit when a drift or data gap surfaces; do not expand integration scope in this cycle.
- **3D assets** – Support the hardware linkage review workflow; ensure candidate/diagnostic heuristics remain conservative and that dashboards can surface the same data.
- **Hardware / product-definition** – Harden the review-item detail link surfaces, link candidates, diagnostics, and now-reconciliation data. Hardware remains the anchor for cross-branch linkages so keep artifacts stable while diagnostics evolve.
- **Cross-branch integrations** – The primary focus is on hardware↔3D and hardware↔reconciliation. Each new integration must re-use the canonical queue/summary/diagnostic naming, and dashboards should treat them identically.

## 6. Integration priorities

1. **Hardware↔3D review workflow** – Already live; keep polishing diagnostics, dashboard linkage points, and status helpers so it continues to demonstrate the pattern for new integrations.
2. **Hardware↔reconciliation review workflow** – Now the second governed pattern; focus on candidate explanation, decision-useful heuristics, and deeper dashboard/review-helper integration so operators trust its advice before any automation arrives.
3. **Cross-branch status helpers** – Update control-plane scripts so they can generically ingest any `_link_review_summary` artifact and display counts.

Why these? They maximize business value (hardware linkage and BOM truths) while letting the control-plane enforce governance before any future pipelines hook into them.

## 7. Drift risks

- **Artifact naming drift** – New manifests or diagnostics using alternative filenames will break dashboard fetchers. Prevention: document every new artifact at rollout time and reuse constants from `docs/system_cohesion.md`.
- **Branch detail divergence** – If a branch starts editing dashboards or queue structures differently, the review workflow loses cohesion. Prevention: require any template change to also update the governance spec and keep review-item fields identical.
- **Policy gate changes sneaking in** – Branch scripts editing `policy.yaml` or `runtime.yaml` would undermine the read-only promise. Prevention: control-plane remains the only owner of those files; branch scripts must emit warnings rather than altering them.

## 8. Smoothest path forward

1. Deepen the reconciliation decision-usefulness layer (normalization, grouping/conflict scaffolding, clearer candidate rankings, review maturity) while keeping the governance-ready artifacts live.
2. Ensure the dashboard overview/branch detail continues to expose the reconciliation counts and review-item detail, reinforcing the read-only surface now that the workflow is mature.
3. Stabilize the reconciliation review helper script so `scripts/control_plane.py summary`/`capabilities` ingest its summary artifact without touching policy files.
4. Once those decision-useful signals are stable, the next cycle can expand to further integrations (e.g., BOM-to-firmware) with confidence because the governance pattern is proven.

This sequence keeps work conservative, reuses established conventions, and protects the orchestrator from drift while each branch deepens only when its artifacts and dashboards are ready.
