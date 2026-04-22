# Architecture Glossary

## Purpose

This glossary standardizes the core terms used across the architecture and roadmap system.

## Terms

### Control plane
The retained orchestration and governance layer responsible for sequencing, qualification, supervision, and release/progression logic.

### Shared runtime substrate
The common execution layer beneath the control plane and domain branches that owns session/job contracts, tools, workspace control, permissions, sandboxing, and artifact behavior.

### Inference gateway
The repo-owned routing layer in front of model backends such as Ollama or optional heavier services.

### Ollama-first
The rule that Ollama is the default local coding route for routine approved implementation work.

### Domain branch
A specialized application or feature family built on top of the shared substrate, such as media control, athlete analytics, environmental monitoring, or repair/restoration support.

### Artifact contract
The standardized set of outputs that a run must emit so validation and promotion systems can compare work consistently.

### Authority surface
A document or system that is authoritative for a particular class of truth, such as architecture truth, roadmap status truth, or release truth.

### CMDB-lite
The repo-owned or limited-scope authoritative inventory/control surface used before a larger CMDB platform is justified.

### Promotion truth
The evidence and authority that determine whether work is qualified for progression or release.

### Grouped execution
Planning and implementing multiple roadmap items together when they share files, systems, or validation surfaces and doing so reduces repeated touches and total effort.

### External system
A third-party or external application, service, protocol, or platform that the system adopts, integrates with, or wraps rather than rebuilding entirely.
