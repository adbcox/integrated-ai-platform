# High Priority Implementation Guide

This guide tracks the immediate execution order for high-leverage roadmap items.

## Active integrated bundle

1. `RM-INTEL-002` — verified OSS capability harvest and compatibility validation
2. `RM-INTEL-001` — watchtower recommendation layer
3. `RM-DEV-005` — local autonomy + adapter/routing governance
4. `RM-DEV-003` — bounded autonomous code generation
5. `RM-DEV-002` — dual-model inline QC loop

## Integration rule

This bundle advances only when all links are present:

- `RM-INTEL-002` validated candidate outcomes are consumed by `RM-INTEL-001`.
- `RM-INTEL-001` + `RM-INTEL-002` recommendation outputs feed `RM-DEV-005`.
- `RM-DEV-005` policy/profile/memory direction feeds bounded execution in `RM-DEV-003`.
- `RM-DEV-002` QC findings classify and feed back into bounded execution artifacts.
