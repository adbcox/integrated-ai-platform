# Roadmap Item Template

Every roadmap item must include:

- stable ID
- title
- category
- type
- status
- priority
- scoring
- scope
- dependencies
- impact
- grouping
- planning / execution / validation linkage
- governance fields
- AI-operability fields
- execution contract fields
- sync metadata

The canonical machine-readable representation lives in `docs/roadmap/items/RM-*.yaml`.

## Canonical `execution_contract` block (required for autonomous pull eligibility)

```yaml
execution_contract:
  autonomous_execution_status: "eligible" # eligible | eligible_with_guardrails | blocked
  next_bounded_slice: "<single bounded executable slice>"
  max_autonomous_scope:
    max_files_touched: 8
    max_loc_delta: 400
    allowed_change_kinds:
      - "code"
      - "schema"
      - "governance_doc"
  validation_contract:
    required_validations:
      - id: "roadmap_consistency"
        command: "python3 bin/validate_roadmap_consistency.py"
        pass_when: "exit_code=0"
    pass_criteria:
      - "All required validations pass."
      - "Validation artifacts are emitted or updated."
  artifact_contract:
    required_artifacts:
      - "artifacts/planning/next_pull.json"
    evidence_outputs:
      - "machine-readable validator output exists"
    machine_readable_outputs:
      - "artifacts/validation/<item>_validation.json"
  completion_contract:
    substep_complete_when:
      - "The bounded change is implemented."
    bounded_slice_complete_when:
      - "Validation contract passes."
      - "Artifact contract outputs exist."
    item_complete_when:
      - "All item slices and DoD evidence are complete."
    blocker_chain_cleared_when:
      - "No directly adjacent in-scope blocker remains."
    small_patch_is_not_completion: true
  truth_surface_updates_required:
    - "docs/roadmap/items/<item-id>.yaml"
    - "artifacts/planning/next_pull.json"
    - "artifacts/planning/blocker_registry.json"
    - "governance/roadmap_dependency_graph.v1.yaml"
  external_dependency_readiness:
    required: false
    readiness_status: "ready" # ready | not_ready | unknown | not_applicable
    blocks_autonomous_execution: false
    blocking_dependencies: []
    notes: ""
```
