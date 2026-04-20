# ADR 0020: Phase 4 Closure — Autonomy Hardening Safety Policy Uplift

**Status**: Ratified
**Package**: CAP-P4-CLOSE-1
**Date**: 2026-04-20
**Authority owner**: governance

## Decision

Phase 4 (Autonomy Hardening Safety Policy Uplift) is declared **closed_ratified**. Phase 5 capability sessions are authorized.

## Evidence

The autonomous retained-edit validation chain was proven with four active gates and full hardening in `bin/stage3_manager.py`:

1. `gate1_syntax_validation` — py_compile for .py; json.loads for .json; sh -n for .sh; pass-through for other types
2. `gate2_target_tests` — naming-convention primary (test_*{stem}*.py); reference-scan fallback (word-boundary grep across test_*.py); bounded smoke fallback (test_stage3_manager_*.py) for zero-coverage targets
3. `gate3_repo_make_check` — repo-wide shell and top-level Python syntax validation via make check
4. `gate4_quick_check_sh` — target-scoped quick_check.sh via direct CLI arg invocation; bin/detect_changed_files.sh implemented with three priority tiers

Additional hardening delivered:
- Revert-failure escalation: all four gates set `classification=revert_failure_dirty_state`, `accepted=False`, `final_status=dirty`, and raise SystemExit on failed git reset
- Gate observability: `target_test_discovery_mode`, `target_test_files_count`, `gates_run` in every trace entry
- Reference-scan discovery recovers coverage for non-conventional targets (`framework/permission_engine.py`, `framework/learning_hooks.py`, etc.)
- Smoke fallback prevents silent no-op Gate 2 for zero-coverage targets

First gate commit: `be45e74`. Final hardening commit: `cb18558`. Gate test count: 81 passing.

## Authority

This ADR ratifies:
- `governance/phase4_closure_evidence.json` (package_id: CAP-P4-CLOSE-1)
- `governance/phase4_closure_decision.json` (decision: closed)

No tactical family is unlocked by this closure.

## Next authorized work

Phase 5 (`qualification_promotion_learning_convergence`) capability sessions may now proceed.
