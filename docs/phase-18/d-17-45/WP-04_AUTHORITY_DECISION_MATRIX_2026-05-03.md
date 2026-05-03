# WP-04 authority decision matrix — 2026-05-03

## Options

| Option | Authority model | Estimated scope | Risk profile |
|---|---|---:|---|
| A | NetBox-only canonical | 30-45h | high migration + semantic compression risk |
| B | inventory.json-only canonical | 16-24h | medium-high governance drift risk |
| C | Hybrid boundary (NetBox intent + inventory runtime + YAML fallback gate) | 12-18h | lowest disruption; aligns with de-facto operations |

## Operator decision

- Decision: **Option C**
- Date: **2026-05-03**
- Locked boundary:
  - NetBox: static asset/network/service catalog intent
  - `~/.platform-registry/inventory.json`: runtime/container/route/dependency state
  - `config/service-registry.yaml.DEPRECATED`: fallback-only until explicit deletion gate

## Execution consequence

- Proceed to WP-05 scope authoring under hybrid model.
- No reconciliation mutations during intake phase.
