# ADR-0002: Typed Tool System

**Status**: accepted  
**Date**: 2026-04-21  
**Phase linkage**: Phase 0 (governance_source_of_truth_reconciliation), Phase 1 (runtime_contract_foundation)  
**Authority sources**: P0-01-AUTHORITY-SURFACE-INVENTORY-1, AS-11-HANDOFF-V7, AS-CW-01, governance/schema_contract_registry.json (framework.tool_schema)

---

## Context

The platform dispatches agent actions through **tools** — discrete callable capabilities with defined input/output contracts. Before this ADR, tool definitions were:
- Implicitly typed via Python function signatures in `framework/`
- Registered in `governance/schema_contract_registry.json` under `framework.tool_schema`
- Referenced by 20+ importers without a governing specification document

The V7 handoff (AS-11-HANDOFF-V7) identified untyped or weakly-typed tool dispatch as a Phase 1 hardening risk. The `framework.tool_schema` entry in the schema registry is an active schema with real importers but lacked an ADR anchor.

The control window adoption packet (AS-CW-01) requires that machine-readable governance artifacts supersede narrative documents. A tool schema ADR is required before Phase 1 can ratify the runtime contract.

---

## Decision

All tools in the platform are **typed** according to the following structure:

```
tool_definition:
  tool_id:          string    # unique, stable identifier
  tool_type:        enum      # read | write | execute | query | governance
  input_schema:     object    # JSON Schema for input parameters
  output_schema:    object    # JSON Schema for output
  permission_level: enum      # none | read_only | write_bounded | write_unbounded | privileged
  idempotent:       bool      # whether repeated calls produce identical outcomes
  side_effects:     list      # declared side effects (file writes, API calls, etc.)
  registered_in:    string    # schema registry key (e.g., "framework.tool_schema")
```

The `framework.tool_schema` entry in `governance/schema_contract_registry.json` is the binding registry reference for all tool definitions. Any tool invoked by the platform runtime must have a registered `tool_id`.

**Tool type semantics**:
- `read`: no side effects; idempotent by definition
- `write`: modifies state; must declare `side_effects`
- `execute`: dispatches external process or agent; may or may not be idempotent
- `query`: retrieves computed or indexed results; idempotent
- `governance`: modifies governance artifacts; requires `permission_level >= write_bounded`

**Permission level enforcement**:
- `none`: available without explicit grant
- `read_only`: requires session-level read grant
- `write_bounded`: requires explicit per-tool grant within a bounded scope
- `write_unbounded`: requires escalation approval
- `privileged`: requires control window sign-off

---

## Consequences

**Positive**:
- Every tool invocation has a traceable schema; debugging and auditing are straightforward
- Permission levels provide a typed gate that `framework/permission_engine.py` can enforce uniformly
- The schema registry entry `framework.tool_schema` now has a governance anchor

**Negative / constraints**:
- All existing tool invocations in `framework/` must be retroactively verified against this schema (Phase 1 work)
- Adding a new `tool_type` value requires a superseding ADR
- `write_unbounded` tools must never be dispatched in a `ratification_only` package class session

**Phase gate impact**:
- Phase 1 runtime contract ratification must verify that `framework.tool_schema` consumers conform to the typed tool structure defined here
- The `governance/schema_contract_registry.json` `framework.tool_schema` entry consumer count must remain accurate
