# Validation Order

Exact execution sequence for safe bounded execution.

## Pre-Execution Phase

1. **Read first_read_files** (from execution control template)
   - CLAUDE.md
   - AGENTS.md
   - docs/roadmap/RM-*_EXECUTION_PACK.md
   - governance/execution_control_template.yaml

2. **Verify artifact_root exists**
   - Confirm `artifacts/` directory exists

3. **Check working tree**
   - Ensure clean git status (no uncommitted changes in non-artifact files)
   - Note: artifacts/ modifications are allowed

## Execution Phase

1. **Syntax validation**
   - `python3 -m py_compile <file>` for any .py files created
   - `python3 -c "import yaml; yaml.safe_load(open('governance/*.yaml'))"` for YAML files

2. **File creation verification**
   - Check all expected_artifacts exist and are readable
   - Verify no files written outside allowed_files

3. **Cross-reference validation**
   - Verify roadmap item IDs in registry.yaml match sync_state.yaml
   - Verify no broken links to governance or roadmap files

4. **Repo validation**
   - `make check` (full syntax validation)
   - `make quick` (fast affected-file checks)

## Post-Execution Phase

1. **Artifact validation**
   - List all created/modified files
   - Verify all expected_artifacts are present
   - Confirm no forbidden_files were modified

2. **Success criteria**
   - All validations pass (no errors)
   - All expected_artifacts exist
   - Git status clean (no unintended modifications)
   - Return rollback_rule if any validation fails

## Failure Recovery

If validation fails:
1. Note which validation step failed
2. Apply rollback_rule immediately
3. Do not proceed further
4. Provide failure summary with exact error
