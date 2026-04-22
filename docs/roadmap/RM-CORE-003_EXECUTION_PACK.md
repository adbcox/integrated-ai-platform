# RM-CORE-003 Execution Pack

## Item Overview

**ID**: RM-CORE-003  
**Title**: Standardize workspace layout  
**Category**: CORE  
**Priority**: P1  
**Phase**: Phase 1

## Execution Objective

Enforce a standard workspace layout with a read-only source checkout, a writable scratch space, and a dedicated artifact root so all execution contexts have a consistent and predictable directory contract.

## Deliverables

1. **Canonical Architecture Baseline** (`governance/canonical_architecture_baseline.yaml`)
   - Subsystem inventory with 18 named subsystems
   - Trust boundary matrix
   - Layer hierarchy and dependency rules
   - Stability levels and lifecycle state

2. **Subsystem Contract Template** (`governance/subsystem_contract_template.yaml`)
   - Reusable contract schema for future subsystem declarations
   - Required fields and example contract

## In Scope

- canonical architecture baseline delivery
- subsystem inventory creation
- trust boundary definition
- subsystem contract template

## Out of Scope

- workspace layout implementation (moved to RM-CORE-003 phase work)
- runtime modifications
- framework changes beyond artifact root contracts

## Allowed Files

- governance/**
- docs/roadmap/**

## Forbidden Files

- bin/**
- framework/**
- tests/**
- .github/**

## Validation Order

1. Parse all YAML files for syntax errors
2. Verify subsystem inventory has minimum 15 subsystems
3. Verify each subsystem has required fields (subsystem_id, name, layer, responsibility, etc.)
4. Verify trust boundary matrix is well-formed
5. Verify subsystem contract template is complete

## Validation Commands

```bash
python3 -c "
import yaml
for f in ['governance/canonical_architecture_baseline.yaml', 'governance/subsystem_contract_template.yaml']:
    with open(f) as fp:
        data = yaml.safe_load(fp)
        print(f'{f}: OK')
"
```

## Rollback Rule

Revert governance/canonical_architecture_baseline.yaml and governance/subsystem_contract_template.yaml to pre-execution state. Remove any related artifacts.

## Artifact Outputs

- governance/canonical_architecture_baseline.yaml
- governance/subsystem_contract_template.yaml

## Integration Points

- RM-CORE-003 architecture baseline consumed by RM-GOV-004 dependency planner
- Subsystem boundaries inform RM-AUTO-002 compiler subsystem scope binding
