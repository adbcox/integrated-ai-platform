# RM-DEV-009 Execution Pack

## Item Overview

**ID**: RM-DEV-009  
**Title**: Agent operating-docs and persistent execution-memory package  
**Category**: DEV  
**Priority**: P1  
**Phase**: Phase 3

## Execution Objective

Create persistent, model-operable agent documentation that reduces token waste and execution ambiguity. Establish the agent-docs layer as reusable reference consumed by execution templates.

## Deliverables

1. **Agent Documentation Layer** (docs/agent/)
   - `commands.md` — Real repo commands only
   - `validation_order.md` — Exact execution sequence
   - `known_failures.md` — Failure patterns + corrections
   - `repo_map.md` — Key directories + purpose

2. **Root Operating Files**
   - `CLAUDE.md` — System role, execution rules, command references
   - `AGENTS.md` — Mission, session discipline, operating rules

## In Scope

- agent-docs directory creation
- commands.md (real commands only, no placeholders)
- validation_order.md (exact execution + validation sequence)
- known_failures.md (common patterns with fixes)
- repo_map.md (key directories and purpose)
- CLAUDE.md updates (operating rules + agent-docs pointers)
- AGENTS.md updates (mission + session requirements)

## Out of Scope

- memory persistence implementation
- execution engine changes
- new tools or commands
- runtime modifications

## Allowed Files

- docs/agent/**
- CLAUDE.md
- AGENTS.md

## Forbidden Files

- framework/**
- bin/**
- tests/**
- .github/**

## Validation Order

1. Verify all docs/agent/ files exist and are readable
2. Verify CLAUDE.md and AGENTS.md exist with required sections
3. Cross-check commands against actual Makefile/scripts
4. Verify no broken links to governance or roadmap files
5. Verify all paths in repo_map.md exist
6. Run: `make check` (syntax validation)

## Validation Commands

```bash
ls docs/agent/*.md && echo "All agent docs exist"
grep -q "commands.md" CLAUDE.md && echo "CLAUDE.md references agent docs"
python3 -c "
import os
for f in ['docs/agent/commands.md', 'docs/agent/validation_order.md', 
          'docs/agent/known_failures.md', 'docs/agent/repo_map.md']:
    assert os.path.exists(f), f'{f} missing'
print('Agent docs: OK')
"
```

## Rollback Rule

Revert docs/agent/, CLAUDE.md, AGENTS.md to pre-execution state. Remove all created files.

## Artifact Outputs

- docs/agent/commands.md
- docs/agent/validation_order.md
- docs/agent/known_failures.md
- docs/agent/repo_map.md
- CLAUDE.md (updated)
- AGENTS.md (updated)

## Integration Points

- RM-DEV-009 agent-docs consumed by RM-DEV-008 memory governance
- RM-DEV-009 pointers in CLAUDE.md guide execution systems to agent-facing docs
- RM-DEV-009 repo_map.md feeds CMDB inventory for architecture
- RM-DEV-009 commands.md validates against actual Makefile targets
- Execution packs for CORE-003, GOV-004, AUTO-002 reference agent-docs structure
