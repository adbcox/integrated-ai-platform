# Component Adoption Download Register

Package: ADOPT-SHORTLIST-LOCK-1  
Date: 2026-04-20  
Authority: governance/authority_adr_0022_component_adoption_decisions.md

This register records every adopted component's source, license, local adapter owner, and whether a download is required now for the active implementation path.

| Component | Decision | Phase | Source URL | License | Local Adapter/Wrapper Owner | Default / Optional / Conditional | Download Required Now? | Notes |
|---|---|---|---|---|---|---|---|---|
| Ollama | mandatory_core | phase1 | https://github.com/ollama/ollama | MIT | internal_inference_gateway | Default | yes | Primary local model manager; required for all inference paths |
| vLLM | approved_optional | phase1_optional | https://github.com/vllm-project/vllm | Apache-2.0 | internal_inference_gateway | Optional | yes | Activate only when OLLAMA_API_BASE_32B routes to vLLM endpoint or Ollama throughput is the bottleneck |
| OpenHands SDK patterns/components | approved_optional | phase2 | https://github.com/All-Hands-AI/OpenHands | MIT | agent_runtime | Optional | yes | Adopt workspace isolation and tool invocation patterns only; do not import the full runtime |
| Aider RepoMap | mandatory_core | phase3 | https://github.com/Aider-AI/aider | Apache-2.0 | shared_runtime_adapter_layer | Default | yes | Required for codebase_repomap.py and AiderExecutor; all calls routed through adapter layer |
| MCP | mandatory_core | phase2 | https://github.com/modelcontextprotocol/specification | MIT | tool_interoperability_layer | Default | yes | All external tool integrations must use MCP protocol boundary |
| Qdrant | mandatory_core | phase2 | https://github.com/qdrant/qdrant | Apache-2.0 | retrieval_and_memory_layer | Default | yes | Vector search backend for RAG stages; all operations routed through retrieval_and_memory_layer |
| gVisor | mandatory_core | phase2 | https://github.com/google/gvisor | Apache-2.0 | sandbox_execution_layer | Default | yes | Required for all code execution paths; no code execution may bypass sandbox_execution_layer |
| SWE-bench | mandatory_core | phase3 | https://github.com/SWE-bench/SWE-bench | MIT | evaluation_wrappers | Default | yes | Required for Codex 5.1 benchmark campaigns and capability gate advancement |
| Backstage | approved_later_phase | phase5 | https://github.com/backstage/backstage | Apache-2.0 | catalog_context_layer | Optional (Phase 5) | no | Approved now; integrate only in Phase 5 when catalog context enrichment is scheduled |
| GLPI | approved_later_phase | phase5 | https://github.com/glpi-project/glpi | GPL-3.0 | cmdb_context_layer | Default (Phase 5) | no | Default CMDB; approved now; integrate only in Phase 5 when CMDB enrichment is a scheduled gate |
| CloudQuery | approved_later_phase | phase5_optional | https://github.com/cloudquery/cloudquery | MPL-2.0 | cmdb_enrichment_layer | Optional (Phase 5) | no | Read-only CMDB enrichment; approved now; integrate alongside GLPI only in Phase 5 if cloud-provider sync is required |
| i-doit | rejected_as_default | phase5_conditional | https://github.com/i-doit/i-doit-open | AGPL-3.0 | none | Rejected default | no | Not adopted as default. Reconsider only if GLPI is operationally rejected or strict ITIL relationship modeling is a hard gate. |
| Firecracker | conditional_only | phase6_plus_conditional | https://github.com/firecracker-microvm/firecracker | Apache-2.0 | sandbox_execution_layer | Conditional | no | Activate only if security review proves gVisor syscall isolation is insufficient; not before Phase 6 |
| Temporal | conditional_only | phase6_plus_conditional | https://github.com/temporalio/temporal | MIT | manager_replacement_or_durability_layer | Conditional | no | Activate only if checkpoint-resume is proven insufficient for cross-session durability; not before Phase 6 |
