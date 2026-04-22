# RM-AUTO-002 Execution Pack

## Item Overview

**ID**: RM-AUTO-002  
**Title**: Roadmap-to-execution compiler baseline  
**Category**: AUTO  
**Priority**: P1  
**Phase**: Phase 3

## Execution Objective

Establish the roadmap-to-execution compiler baseline that transforms selected roadmap items into execution-ready bundles with preserved roadmap ID, scope, validations, rollback rules, and artifact expectations.

## Deliverables

1. **Execution Bundle Schema** (`governance/execution_bundle_schema.yaml`)
   - Machine-readable schema for execution bundles
   - Required fields specification
   - Field definitions with types and examples
   - Example compiled bundle

2. **Roadmap Compiler** (`bin/roadmap_compiler.py`)
   - Runnable Python script
   - Reads live roadmap items
   - Produces execution bundles
   - Preserves roadmap ID and governance fields
   - Binds subsystems from architecture baseline

3. **Example Compiled Bundle** (`artifacts/compiled_bundles/example_rm_dev_005_bundle.json`)
   - Real compiled bundle for RM-DEV-005
   - Demonstrates all required fields
   - Shows subsystem binding integration
   - Suitable for prompt-builder input

## In Scope

- execution bundle schema definition
- compiler implementation
- subsystem binding from architecture
- example bundle generation
- roadmap ID preservation

## Out of Scope

- prompt-builder implementation
- bundle execution runtime
- Plane sync integration

## Allowed Files

- governance/**
- bin/**
- artifacts/**

## Forbidden Files

- framework/**
- tests/**
- config/**
- .github/**

## Validation Order

1. Parse execution_bundle_schema.yaml for syntax
2. Verify schema includes all required fields
3. Verify python syntax: `python3 -m py_compile bin/roadmap_compiler.py`
4. Run compiler on RM-DEV-005: `python3 bin/roadmap_compiler.py RM-DEV-005`
5. Verify example bundle contains all required fields
6. Verify bundle validates against schema
7. Verify roadmap_id is preserved

## Validation Commands

```bash
python3 -m py_compile bin/roadmap_compiler.py
python3 bin/roadmap_compiler.py RM-DEV-005 > /tmp/bundle.json
python3 -c "
import json
b = json.load(open('/tmp/bundle.json'))
required = ['bundle_id', 'roadmap_id', 'objective', 'scope', 'allowed_files', 'forbidden_files', 'validation_order', 'rollback_rule', 'expected_artifacts', 'execution_instructions']
for field in required:
    assert field in b, f'Missing {field}'
assert b['roadmap_id'] == 'RM-DEV-005'
print('OK')
"
```

## Rollback Rule

Revert governance/execution_bundle_schema.yaml, bin/roadmap_compiler.py, and artifacts/compiled_bundles/example_rm_dev_005_bundle.json to pre-execution state.

## Artifact Outputs

- governance/execution_bundle_schema.yaml
- bin/roadmap_compiler.py
- artifacts/compiled_bundles/example_rm_dev_005_bundle.json

## Integration Points

- Compiler depends on RM-CORE-003 architecture baseline for subsystem binding
- Compiler depends on RM-GOV-004 planner for dependency state
- Bundle output suitable for downstream prompt-builder and execution engine
- Bundles preserve all governance constraints from source roadmap items
