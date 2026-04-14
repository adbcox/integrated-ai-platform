# Level 7 roadmap for manager and retrieval stacks

The Stage-6 preview lane is the first step past the dual-file Stage-5 workload. We now define **Level 6** as the current capability (sequential Stage-5 jobs driven by Manager-5, Stage RAG-4 plans, and the promotion trace schema). **Level 7** is the next architectural milestone.

## Manager Level 7 definition

A Level 7 manager must:

1. route between production/candidate/preview lanes explicitly with manifest-aware metadata.
2. decompose a broader plan into bounded Stage-5 subjobs while tracking their provenance.
3. bundle related targets safely (via Stage-6 plans) and expose retries/refinement paths.
4. persist plan histories + statuses for promotion audits and future tuning.
5. emit trace metadata that records the plan id, job outcomes, and failure/refine hints.

### Level 7 gap and next step (implemented here)

*Gap:* Stage-6 could plan jobs but had no persisted history or fallback path.
*Next step implemented:* Manager-5 now writes a plan history file (`artifacts/manager5/plans/{plan_id}.json`), includes plan payload/provenance in traces, and supports a `--fallback-target` so the lane can run even when RAG-4 returns no candidates.
It also now filters Stage-6 targets by their RAG-4 `confidence` score (`--min-confidence`) and automatically retries failed plans with a fallback target, recording the retry reason in the plan record.

## RAG Level 7 definition

A Level 7 retrieval stack must:

1. identify primary files reliably (via lexical, structural, and git-history signals).
2. surface companion files with explicit relatedness metadata and preview snippets.
3. package the planning context (query, provenance, related limits) that broader managers can consume.
4. keep planning-only guarantees intact while enabling future layers to refine the plan.

### Level 7 gap and next step (implemented here)

*Gap:* Stage RAG-4 provided targets but no provenance or payload packaging.
*Next step implemented:* The Stage RAG-4 planner now records `provenance` data (tokenized query, limits) and includes the raw payload so managers can inspect why each target was suggested.
It also attaches per-target `confidence` and `related_score` metadata so the manager can drop weak companions before they reach execution.

## Forward plan toward Level 7

1. Add richer retry/refinement guards in Manager-5 (e.g., mark failed jobs for rerun, flag future attempt windows).  
2. Expose plan previews (diff snippets, related companion context) so operators can inspect before executing Stage-5 jobs.  
3. Enhance RAG-4 to rank companions so managers can group targets by shared anchors or recent co-edits.  
4. Add tooling that reads `artifacts/manager5/plans/` to feed dashboards or automated readiness checks.

When the plan history is reviewed, companion files consistently help Stage-6 job sequencing, and the manager can reroute/ retry failed jobs with bounded adjustments, both stacks can be considered Level 7.
