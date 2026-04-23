# Hardware Capability and Constraints

## Purpose

This document is the repository’s **hardware source of truth** for the governed local-execution platform.

It exists to answer, in one place:
- what hardware is currently available to the system
- what each hardware asset is good for
- what each hardware asset should **not** be used for
- what current bottlenecks, risks, and firmware/compatibility concerns exist
- what hardware gaps most constrain the roadmap and local-execution posture

This document is intended for:
- operators
- control windows
- execution windows
- local coding assistants
- future inventory/CMDB and procurement workflows

## Authority and usage

This is an **operating / capability truth surface**, not a replacement for canonical roadmap item truth.

Use this document when work depends on hardware realities such as:
- model selection
- local inference capacity
- Apple/Xcode capability
- GPU/VRAM constraints
- storage availability
- workstation role selection
- firmware and driver caveats
- upgrade-priority decisions

When actual live hardware facts are updated, this document should be revised directly and then referenced by future chats and coding assistants.

## Current status

**Status:** active, incomplete, and intended to be continuously hardened.

Important current note:
- this document is designed to be robust even when some exact inventory details are still missing
- any field not yet confirmed should be marked `unknown`, `to_capture`, or `needs_validation`
- unknowns should not be silently assumed by coding assistants

## How to read this document

Read in this order:

1. executive hardware posture
2. critical hardware constraints affecting roadmap/workflow decisions
3. system-by-system asset inventory
4. current gaps and immediate concerns
5. update protocol and required capture fields

## Executive hardware posture

The platform depends on a mixed hardware estate that likely includes some combination of:
- local AI/inference-capable machines
- coding/development workstations
- Apple/macOS/Xcode-capable machines
- storage/NAS or persistent local data hosts
- networking and remote-access equipment
- dashboard/tablet/display endpoints
- home-automation bridge hardware
- peripheral GPUs, compute cards, or graphics-capable systems

This document should ultimately classify each asset into one or more of these roles:
- `primary_local_inference_host`
- `primary_local_dev_host`
- `apple_dev_host`
- `automation_orchestrator_host`
- `storage_or_dataset_host`
- `remote_access_entrypoint`
- `dashboard_or_voice_endpoint`
- `spare_or_lab_system`

## Current hardware-driven planning rules

### 1. Do not assume model capacity
If GPU/VRAM/RAM/CPU/storage details are not explicitly recorded here, assistants must not assume that a model or workload fits.

### 2. Do not assume Apple build capability
If the specific macOS/Xcode-capable machine and its current readiness state are not recorded here, Apple-targeted execution must be treated as environment-dependent.

### 3. Firmware and driver state matter
Motherboard BIOS, GPU driver, chipset firmware, storage firmware, and OS version can materially change:
- model compatibility
- CUDA/Metal/ROCm posture
- Apple build reliability
- stability under sustained local workloads

### 4. Procurement should be tied to gaps, not hype
Upgrade and purchase decisions should be justified using actual constraints documented here.

## Asset inventory model

Each asset entry should be recorded using the following template.

### Required fields per asset
- `asset_id`
- `friendly_name`
- `asset_type`
- `primary_role`
- `secondary_roles`
- `owner_or_location`
- `current_status`
- `operating_system`
- `cpu_model`
- `cpu_cores_threads`
- `ram_total`
- `ram_type`
- `gpu_model`
- `gpu_vram`
- `motherboard_model`
- `chipset`
- `storage_devices`
- `networking_notes`
- `firmware_bios_state`
- `driver_runtime_state`
- `local_ai_relevance`
- `coding_relevance`
- `limits_and_risks`
- `preferred_future_use`
- `validation_status`
- `last_verified`

## Canonical asset template

```yaml
asset_id: HW-000
friendly_name: ""
asset_type: workstation | server | laptop | mini_pc | nas | tablet | network_device | peripheral | gpu | display | other
primary_role: ""
secondary_roles: []
owner_or_location: ""
current_status: active | standby | degraded | lab_only | retired | unknown
operating_system:
  name: ""
  version: ""
  notes: ""
cpu:
  model: ""
  cores_threads: ""
  notes: ""
ram:
  total: ""
  type: ""
  notes: ""
gpu:
  model: ""
  vram: ""
  notes: ""
motherboard:
  model: ""
  chipset: ""
  notes: ""
storage_devices: []
networking_notes: ""
firmware_bios_state:
  version: ""
  update_status: current | outdated | unknown | needs_validation
  notes: ""
driver_runtime_state:
  graphics_driver: ""
  ai_runtime_notes: ""
  update_status: current | outdated | unknown | needs_validation
local_ai_relevance:
  role: ""
  supported_workloads: []
  blocked_workloads: []
coding_relevance:
  role: ""
  supported_workloads: []
  blocked_workloads: []
limits_and_risks: []
preferred_future_use: []
validation_status: confirmed | partial | unknown
last_verified: ""
```

## Inventory sections

The sections below should be populated as details are confirmed.

### 1. Primary local AI / inference hosts
Use this section for machines expected to run:
- Ollama
- local planning models
- local Aider-backed coding assistance
- vector/search or orchestration components when relevant

#### Capture priorities
- exact GPU model
- exact VRAM
- exact RAM capacity
- cooling/stability concerns
- storage throughput constraints
- whether the box should host Tier S / Tier M / Tier H local models

#### Current entries

##### AI Host 1
- asset_id: `to_capture`
- friendly_name: `to_capture`
- status: `unknown`
- notes: exact model and role not yet captured in this document

### 2. Primary development workstations
Use this section for machines used for:
- repo work
- Aider / terminal workflows
- document/governance work
- testing and validation

#### Capture priorities
- OS version
- shell/dev tooling state
- editor/terminal posture
- repo storage location/performance
- whether remote relay should target this machine

#### Current entries

##### Dev Host 1
- asset_id: `to_capture`
- friendly_name: `to_capture`
- status: `unknown`
- notes: exact workstation specification and current environment posture need capture

### 3. Apple / Xcode-capable hosts
Use this section for any system intended for:
- Xcode
- Apple build/test/signing flows
- macOS-specific development

#### Capture priorities
- exact Apple model
- SoC / CPU generation
- RAM
- macOS version
- Xcode version
- signing/toolchain readiness
- whether this is the canonical Apple execution host

#### Current entries

##### Apple Host 1
- asset_id: `to_capture`
- friendly_name: `to_capture`
- status: `unknown`
- notes: required for strong `RM-DEV-001` posture; exact host must be recorded here

### 4. Storage / data / backup hosts
Use this section for:
- NAS systems
- large local data repositories
- backup targets
- artifact retention and dataset storage

#### Capture priorities
- storage capacity
- RAID/ZFS or equivalent posture
- backup role
- uptime/reliability state
- network access constraints

#### Current entries

##### Storage Host 1
- asset_id: `to_capture`
- friendly_name: `to_capture`
- status: `unknown`
- notes: exact storage and backup host posture needs capture

### 5. Networking / remote-access / edge hosts
Use this section for:
- routers/gateways relevant to remote work
- Tailscale/VPN or relay entry points
- reverse proxies
- remote shell/workspace exposure systems

#### Capture priorities
- remote access method
- security posture
- reliability and latency constraints
- whether this is the canonical remote operator path

#### Current entries

##### Remote Access Entry 1
- asset_id: `to_capture`
- friendly_name: `to_capture`
- status: `unknown`
- notes: remote operator continuity depends on this being explicitly captured

### 6. Dashboard / tablet / voice / ambient endpoints
Use this section for:
- keep tablets / displays
- voice endpoints
- kitchen/hallway/entertainment displays
- ambient assistant surfaces

#### Capture priorities
- device model
- mount/use location
- screen size/resolution
- battery or power posture
- operating system / kiosk mode posture
- future UI role

#### Current entries

##### Ambient Endpoint 1
- asset_id: `to_capture`
- friendly_name: `to_capture`
- status: `unknown`
- notes: required for future dashboard and voice/ambient rollout

### 7. Spare, lab, and candidate-repurpose systems
Use this section for:
- underused PCs
- spare GPUs
- test rigs
- machines that may become inference, orchestration, or storage hosts

#### Capture priorities
- actual condition
- redeployment opportunity
- upgrade blockers
- resale vs repurpose decision

#### Current entries

##### Lab System 1
- asset_id: `to_capture`
- friendly_name: `to_capture`
- status: `unknown`
- notes: useful for gap analysis and procurement avoidance

## Capability classification model

Each asset should also receive explicit capability tags.

### Example capability tags
- `can_run_tier_s_local_models`
- `can_run_tier_m_local_models`
- `can_run_tier_h_local_models`
- `suitable_for_aider_default_host`
- `suitable_for_remote_terminal_anchor`
- `suitable_for_xcode_primary`
- `suitable_for_docker_openhands`
- `suitable_for_storage_and_artifacts`
- `suitable_for_dashboard_endpoint`
- `not_suitable_for_sustained_local_inference`
- `not_suitable_for_gpu_accelerated_models`

## Current gaps and immediate concerns

This section should become the operator-facing “what is missing” view.

### Immediate hardware questions that must be answered
1. Which exact machine is the canonical local AI host?
2. Which exact machine is the canonical primary development host?
3. Which exact machine is the canonical Apple/Xcode host?
4. What exact GPU(s) and VRAM capacities are available now?
5. What motherboard/chipset/BIOS versions matter for stability or upgrade planning?
6. What current firmware, driver, or OS issues could block local AI or coding execution?
7. Which systems are suitable for remote operator continuity away from home?
8. Which spare systems can be repurposed before new purchases are made?

### Hardware risk categories to maintain
- `capacity_gap`
- `firmware_unknown`
- `driver_unknown`
- `thermal_or_power_risk`
- `storage_insufficient`
- `network_remote_access_risk`
- `apple_toolchain_gap`
- `gpu_vram_gap`
- `single_point_of_failure`

## Procurement and upgrade decision support

This document should directly support procurement discussions.

Before recommending hardware purchases, assistants should use this document to answer:
- what asset is currently acting as the bottleneck
- whether the limitation is GPU, RAM, storage, networking, or firmware/tooling
- whether a repurpose option exists before buying new hardware
- whether a firmware/driver/OS update would solve the issue without new hardware

## Update protocol

### When to update this document
Update whenever:
- a new machine is added
- an existing machine is repurposed
- a GPU or motherboard is changed
- firmware/BIOS/driver state changes materially
- an asset is retired or moved to lab-only state
- a new hardware bottleneck is identified

### How unknowns should be captured
Use only:
- `unknown`
- `to_capture`
- `needs_validation`

Do not silently infer exact hardware details.

### Validation sources to use when available
- system profiler outputs
- BIOS/UEFI version screens
- GPU utility output
- `ollama ps` / local runtime outputs where relevant
- OS-level hardware reports
- purchase records or photographed labels if needed

## Relationship to roadmap items

This document is especially relevant to:
- `RM-INV-002`
- `RM-INV-003`
- `RM-DEV-001`
- `RM-UI-005`
- `RM-OPS-004`
- `RM-OPS-005`
- `RM-OPS-008` if remote operator workspace/relay work is added or active

## Notes

This document should become the single best answer to the question:

> what hardware do we actually have, what can it realistically do, what should it be used for, and what is currently limiting us?

It is intentionally structured to be useful even before every exact model has been captured.
