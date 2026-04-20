# RGC Naming Policy

## Roadmap item IDs

Pattern: `RM-<DOMAIN>-<NNN>`

- `RM` — fixed prefix
- `<DOMAIN>` — uppercase domain token from the category set (e.g. `CORE`, `OPS`, `GOV`)
- `<NNN>` — zero-padded three-digit sequence number

Valid examples:
- `RM-CORE-001`
- `RM-OPS-042`
- `RM-GOV-007`

Invalid examples:
- `RM-core-001` (lowercase domain)
- `RM-CORE-1` (sequence not zero-padded to 3 digits)
- `CORE-001` (missing `RM-` prefix)

Validated by: `roadmap_governance/parser.py::validate_naming`
Finding type on violation: `naming_violation` (severity: error)

## CMDB canonical names

Pattern: `<seg>.<seg>[.<seg>...]`

- Two or more dot-separated segments
- Each segment: `[a-z0-9][a-z0-9-]*` (lowercase, alphanumeric, hyphens allowed, must start with alphanumeric)
- Convention: `<environment>.<domain>.<service>` (three-segment) or `<domain>.<service>` (two-segment)

Valid examples:
- `prod.rgc.api`
- `staging.rgc.worker`
- `homelab.dns`

Invalid examples:
- `api` (single segment)
- `Prod.RGC.API` (uppercase)
- `prod..api` (empty segment)
- `prod.rgc.api.` (trailing dot)

Validated by: `roadmap_governance/cmdb_service.py::validate_canonical_name`
Finding type on violation: `invalid_canonical_name` (severity: error)

## CMDB entity types

Allowed values (enforced by import validation):
- `machine`
- `service`
- `repo`
- `script`
- `dashboard`
- `dataset`
- `device`

Finding type on violation: `invalid_entity_type` (severity: warning)

## Roadmap item categories

Allowed values (enforced by integrity review):

| Token | Domain |
|---|---|
| `GOV` | Governance |
| `CORE` | Core platform |
| `DEV` | Developer tooling |
| `UI` | User interface |
| `AUTO` | Automation |
| `OPS` | Operations |
| `INV` | Inventory |
| `MEDIA` | Media |
| `HOME` | Home automation |
| `LANG` | Language/ML |
| `HW` | Hardware |
| `SHOP` | Shopping |
| `AUTO-MECH` | Automotive/mechanical |
| `DOCAPP` | Document applications |
| `INTEL` | Intelligence/analytics |

Finding type on violation: `invalid_category` (severity: warning)

## Roadmap item types

Allowed values:
- `platform_foundation`
- `capability`
- `workflow`
- `integration`
- `interface`
- `infrastructure`
- `research`
- `governance`
- `automation`
- `hardware`
- `domain_app`

Special value: `unknown` is a placeholder for markdown-only items and is exempt from the type check.

Finding type on violation: `invalid_item_type` (severity: warning)

## Roadmap item priorities

Allowed values: `P0`, `P1`, `P2`, `P3`, `P4`

Finding type on violation: `invalid_priority` (severity: warning)

## Feature-block package IDs

Pattern: `PKG-<CATEGORY>`

Generated automatically by the planner: `PKG-` + category.upper(). One package per category. Stable across reruns.

Examples:
- `PKG-CORE`
- `PKG-OPS`
- `PKG-GOV`
