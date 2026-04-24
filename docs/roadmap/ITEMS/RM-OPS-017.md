# RM-OPS-017

- **ID:** `RM-OPS-017`
- **Title:** Service mesh integration (Istio/Linkerd)
- **Category:** `OPS`
- **Type:** `Enhancement`
- **Status:** `Accepted`
- **Maturity:** `M0`
- **Priority:** `Medium`
- **Priority class:** `P3`
- **Queue rank:** `17`
- **Target horizon:** `near-term`
- **LOE:** `M`
- **Strategic value:** `3`
- **Architecture fit:** `4`
- **Execution risk:** `3`
- **Dependency burden:** `2`
- **Readiness:** `near`

## Description

Integrate service mesh (Istio or Linkerd) for advanced traffic management. Enable circuit breaking, retries, and observability.

## Why it matters

Service mesh enables:
- intelligent traffic management
- circuit breaking and resilience
- mutual TLS encryption
- advanced monitoring and tracing
- gradual rollouts and canary deployments

## Key requirements

- service mesh installation and management
- virtual service and destination rules
- traffic policies and routing
- circuit breaker configuration
- mutual TLS setup
- integration with observability

## Affected systems

- infrastructure
- networking
- observability

## Expected file families

- istio/ — service mesh configuration
- istio/virtualservices/ — traffic rules
- istio/policies/ — traffic policies
- config/mesh_config.yaml — mesh configuration

## Dependencies

- `RM-OPS-011` — Kubernetes manifests

## Risks and issues

### Key risks
- service mesh complexity and overhead
- debugging difficulties with mesh
- performance impact of sidecar proxies

### Known issues / blockers
- none; ready to start

## CMDB / asset linkage

- Istio, Linkerd, service mesh

## Grouping candidates

- none (depends on `RM-OPS-011`)

## Grouped execution notes

- Blocked by `RM-OPS-011`. Builds on Kubernetes.

## Recommended first milestone

Install and configure service mesh with basic traffic policies.

## Status transition notes

- Expected next status: `In progress`
- Transition condition: service mesh with traffic policies
- Validation / closeout condition: service mesh deployed for core services

## Notes

Advanced infrastructure for microservices.
