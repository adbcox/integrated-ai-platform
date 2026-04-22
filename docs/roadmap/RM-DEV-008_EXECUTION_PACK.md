# RM-DEV-008 Execution Pack

## Item Overview

**ID**: RM-DEV-008  
**Title**: Memory governance, summarization, and provenance policy for the local agent  
**Category**: DEV  
**Priority**: P1  
**Phase**: Phase 3

## Execution Objective

Define explicit memory governance rules that distinguish between root memory, modular docs, scoped rules, and known-failures. Create machine-readable provenance policy for execution-memory persistence.

## Deliverables

1. **Memory Classification Schema** (`governance/memory_classification.yaml`)
   - Four memory tiers: root / modular / scoped / known-failures
   - Classification rules with examples
   - Validation boundaries per tier

2. **Memory Provenance Policy** (`governance/memory_provenance_policy.yaml`)
   - Authority rules (who decides what persists)
   - Summarization policy (what compresses, what stays verbatim)
   - Audit trail requirements
   - Rollback policy per memory tier

3. **Memory Governance Documentation** (`docs/agent/memory_governance.md`)
   - Human-readable memory policy
   - Decision flowchart for persistence decisions
   - Examples of root vs. ephemeral decisions

## In Scope

- memory classification schema (root / modular / scoped / known-failures)
- provenance policy (who decides what persists)
- summarization rules (what compresses, what stays)
- validation boundaries (gates for persistence)
- governance documentation

## Out of Scope

- runtime memory management implementation
- execution engine changes
- model training or fine-tuning
- new persistence backends

## Allowed Files

- governance/**
- docs/agent/**

## Forbidden Files

- framework/**
- bin/**
- tests/**
- .github/**

## Validation Order

1. Parse memory_classification.yaml for syntax
2. Parse memory_provenance_policy.yaml for syntax
3. Verify memory tiers are defined (root / modular / scoped / known-failures)
4. Verify provenance rules are unambiguous
5. Verify no circular dependencies in governance rules
6. Cross-reference with RM-DEV-009 agent-docs
7. Run: `make check` (syntax validation)

## Validation Commands

```bash
python3 -c "
import yaml
for f in ['governance/memory_classification.yaml', 'governance/memory_provenance_policy.yaml']:
    with open(f) as fp:
        data = yaml.safe_load(fp)
        print(f'{f}: OK')
        
# Verify memory tiers
import yaml
mc = yaml.safe_load(open('governance/memory_classification.yaml'))
tiers = {t['tier'] for t in mc.get('memory_tiers', [])}
required = {'root', 'modular', 'scoped', 'known_failures'}
assert required.issubset(tiers), f'Missing tiers: {required - tiers}'
print('Memory tiers: OK')
"
```

## Rollback Rule

Revert governance/memory_*.yaml and docs/agent/memory_governance.md to pre-execution state.

## Artifact Outputs

- governance/memory_classification.yaml
- governance/memory_provenance_policy.yaml
- docs/agent/memory_governance.md

## Integration Points

- RM-DEV-008 depends on RM-DEV-009 agent-docs for documentation patterns
- RM-DEV-008 consumes RM-CORE-003 architecture baseline for subsystem boundaries
- RM-DEV-008 consumes RM-GOV-004 dependency graph for state management rules
- RM-DEV-008 enables bounded execution with auditable memory policy
- Execution systems reference memory_provenance_policy.yaml for persistence decisions
