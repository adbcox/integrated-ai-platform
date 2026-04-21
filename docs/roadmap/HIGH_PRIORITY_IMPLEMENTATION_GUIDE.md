# High Priority Implementation Guide

This guide tracks the immediate execution order for high-leverage roadmap items.

## Current priority pair

1. `RM-DEV-003` — bounded autonomous code generation baseline
2. `RM-INTEL-001` — OSS watchtower with update alerts and adoption recommendations

## Integrated execution rule

These two items should be implemented as one bounded slice:

- `RM-DEV-003` defines what bounded autonomous coding needs.
- `RM-INTEL-001` tracks which OSS components can satisfy those needs safely.
- linkage artifacts must map capability needs to candidate recommendations.

## Minimum acceptance baseline

- bounded autonomous task contract and run artifact structure are machine-readable
- OSS watchtower candidate registry is machine-readable with recommendation classes
- at least one linkage artifact maps RM-DEV-003 needs to RM-INTEL-001 candidates
- machine-readable validation artifact proves required fields and cross-file consistency
