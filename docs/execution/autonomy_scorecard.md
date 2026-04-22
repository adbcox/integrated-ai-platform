# Autonomy Scorecard — Execution Gate

schema_version: 1  
authority: docs/execution/autonomy_scorecard.md  
ratified_by: RM-GOV-007  
source_surface: governance/autonomy_scorecard.v1.yaml

## Purpose

Define the binding readiness scorecard used to evaluate autonomy progression and promotion readiness for governed local-first execution.

## Required dimensions

1. **First-pass success rate**
   - Measures fraction of tasks passing on first attempt without retry/fallback/escalation.
2. **Retry count**
   - Measures average retries per task before passing outcome.
3. **Escalation rate**
   - Measures fraction of package steps requiring escalation.
4. **Code-outcome coverage**
   - Tracked via validation pass-rate over declared validation order.
5. **Artifact completeness**
   - Measures fraction of declared artifacts that exist, parse, and match expected identity.
6. **Promotion readiness**
   - Boolean gate indicating all blocking progression rules satisfied.

## Threshold bands

- **first_pass_success**: target `>=0.85`, warning `<0.85`, blocking `<0.50`
- **retry_count**: target `<=0.0`, warning `>1.0`, blocking `>3.0`
- **escalation_rate**: target `<=0.0`, warning `>0.10`, blocking `>0.25`
- **artifact_completeness**: target `1.0`, warning `<0.95`, blocking `<0.90`
- **validation_pass_rate**: target `>=0.90`, warning `<0.70`, blocking `<0.50`
- **promotion_readiness**: must be `true`; any blocking-rule failure sets `false`

## Interpretation gates

- **good**: all metrics in target bands and promotion readiness satisfied.
- **caution**: warning-band metrics present, no blocking-band metrics.
- **failing**: one or more blocking thresholds breached.
- **regression_detected**: current metrics materially below baseline warning bands.

## Phase linkage

- Phase progression and local-autonomy gating rules are defined in:
  - `governance/autonomy_scorecard.v1.yaml`
- Definition-of-done linkage remains authoritative at:
  - `docs/execution/definition_of_done.md`

## Enforcement note

This document is the execution-facing summary and ratification surface.  
Machine-readable scoring logic and rule evaluation remain in `governance/autonomy_scorecard.v1.yaml`.
