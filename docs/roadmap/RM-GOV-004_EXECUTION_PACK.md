# RM-GOV-004 Execution Pack

## Item Overview

**ID**: RM-GOV-004  
**Title**: Create machine-readable execution-control package  
**Category**: GOV  
**Priority**: P1  
**Phase**: Phase 0

## Execution Objective

Formalize the machine-readable execution-control package schema with required fields and deliver a roadmap dependency planner that computes blocked/unblocked state over live roadmap items.

## Deliverables

1. **Roadmap Dependency Graph** (`governance/roadmap_dependency_graph.yaml`)
   - Machine-readable dependency graph schema
   - All roadmap items as nodes with dependency information
   - Dependency edges with hard/soft distinction
   - Computed blocked/unblocked state
   - Next-pull ordering with priority scoring

2. **Roadmap Dependency Planner** (`bin/roadmap_dependency_planner.py`)
   - Runnable Python script
   - Reads live roadmap items from filesystem
   - Computes blocked vs unblocked state
   - Generates next-pull ordering
   - Outputs structured JSON

## In Scope

- roadmap dependency graph schema definition
- dependency planner implementation
- blocked/unblocked state computation
- next-pull ordering logic
- live roadmap integration

## Out of Scope

- runtime enforcement of dependencies
- auto-generation of packages
- Plane sync integration
- governance enforcement

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

1. Parse roadmap_dependency_graph.yaml for syntax
2. Verify graph schema includes all required fields
3. Verify python syntax: `python3 -m py_compile bin/roadmap_dependency_planner.py`
4. Run planner: `python3 bin/roadmap_dependency_planner.py`
5. Verify planner output contains unblocked_list and next_pull_ordering
6. Verify dependency graph correctness by spot-checking blocked/unblocked state

## Validation Commands

```bash
python3 -m py_compile bin/roadmap_dependency_planner.py
python3 bin/roadmap_dependency_planner.py > /tmp/plan.json
python3 -c "import json; data = json.load(open('/tmp/plan.json')); assert 'next_pull_ordering' in data; assert len(data['unblocked_list']) >= 5; print('OK')"
```

## Rollback Rule

Revert governance/roadmap_dependency_graph.yaml and bin/roadmap_dependency_planner.py to pre-execution state.

## Artifact Outputs

- governance/roadmap_dependency_graph.yaml
- bin/roadmap_dependency_planner.py

## Integration Points

- Planner output consumed by RM-AUTO-002 compiler for bundle compilation
- Dependency graph visualizes roadmap state at all times
- Next-pull ordering informs execution planning
