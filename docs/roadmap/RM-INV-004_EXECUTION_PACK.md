# RM-INV-004 — Execution Pack

## Title

**RM-INV-004 — CMDB service/application/dependency topology and capability graph**

## Objective

Deepen the CMDB into a topology and capability graph that models services, applications, data stores, hosts, dependencies, and what capabilities they enable.

## Why this matters

The platform needs more than asset lists. It needs a dependency-aware graph that explains what depends on what and what is blocked or enabled by each component.

## Required outcome

- service/application topology model
- dependency graph
- capability graph
- ownership and environment linkage
- roadmap linkage to topology nodes

## Required artifacts

- CMDB topology schema
- dependency graph model
- capability linkage model
- environment/service map
- topology validation report

## Best practices

- distinguish physical assets, logical services, and capabilities
- preserve stable IDs for graph nodes
- link topology back to roadmap items and execution systems
- keep the graph queryable for pull planning and impact analysis

## Common failure modes

- CMDB that is just a flat inventory
- no distinction between dependency and capability relationships
- topology docs with no machine-readable representation

## Recommended first milestone

Define the topology graph schema and model one critical system slice spanning local agent, runtime, memory, and UI dependencies.
