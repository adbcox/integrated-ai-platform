# Hardware Capture and Validation Runbook

## Purpose

This runbook defines how to capture, validate, and maintain hardware facts for the governed local-execution platform.

It turns the hardware governance documents into an operational process.

Use this runbook when:
- onboarding a new hardware asset
- validating an existing asset
- confirming firmware, driver, or OS state
- updating hardware roles after repurpose or upgrade
- investigating a hardware bottleneck or capability question

## Companion documents

Use with:
- `docs/governance/HARDWARE_CAPABILITY_AND_CONSTRAINTS.md`
- `docs/governance/hardware_inventory_registry.yaml`
- `docs/governance/DOCUMENT_STATE_INDEX.md`

## Capture objectives

For each relevant hardware asset, capture enough data to answer:
- what it is
- where it is
- what it can run
- what it should not run
- what firmware/driver/OS constraints matter
- whether it is suitable for local AI, coding, Apple builds, storage, remote access, or dashboard roles

## Validation states

Use only:
- `confirmed`
- `partial`
- `unknown`

### confirmed
Use when the specification or state has been checked directly from the machine, authoritative management UI, or trusted records.

### partial
Use when some fields are verified but others remain missing or inferred.

### unknown
Use when the asset exists conceptually but the details are not yet confirmed.

## Capture sequence by asset type

### 1. Workstations / servers / laptops
Capture:
- hostname / friendly name
- OS and version
- CPU model
- RAM capacity and type
- GPU model and VRAM
- motherboard model and chipset where applicable
- BIOS/UEFI version
- local storage devices and capacity
- current local AI role
- coding role
- limits / risks / thermal notes

### 2. Apple/macOS hosts
Capture:
- exact Apple model
- SoC / CPU generation
- RAM/unified memory
- macOS version
- Xcode version
- toolchain or signing notes
- primary Apple role
- any constraints on local AI or Apple build work

### 3. Storage/NAS hosts
Capture:
- platform/model
- total storage and pool layout
- RAID/ZFS or equivalent notes
- backup role
- network path/access notes
- firmware/OS version
- risk notes and single-point-of-failure concerns

### 4. Network / remote access devices
Capture:
- device model
- role in remote operator continuity
- VPN/Tailscale/reverse-proxy posture
- firmware version
- security notes
- reliability and latency constraints

### 5. Dashboard / voice / tablet endpoints
Capture:
- device model
- screen size/resolution
- location/use case
- OS/kiosk state
- power/battery notes
- future UI/voice role

## Recommended validation sources

Prefer direct, authoritative sources such as:
- OS hardware reports
- BIOS/UEFI screens
- vendor control panels or management apps
- system profiler outputs
- Apple “About This Mac” / system report
- GPU utilities
- purchase records or photographed labels
- trusted management interfaces for NAS/network devices

## Example capture command categories

These are examples of categories to use when collecting data. Adapt per host/OS.

### Linux / general workstation
- CPU info
- memory info
- GPU info
- storage layout
- BIOS/firmware info
- OS version
- network identity

### macOS
- system profiler
- hardware overview
- graphics/display report
- storage report
- software/Xcode versions

### Local AI hosts
Also capture:
- local runtime posture
- model-serving notes
- whether the host is intended for Tier S / Tier M / Tier H workloads
- thermal or sustained-load concerns

## Required update workflow

1. identify asset to capture or update
2. collect direct facts from authoritative source
3. update `hardware_inventory_registry.yaml`
4. update `HARDWARE_CAPABILITY_AND_CONSTRAINTS.md` summary sections if the change affects posture, gaps, or future-use guidance
5. set `validation_status`
6. update `last_verified`
7. note any newly discovered gap, risk, or repurpose opportunity

## Minimum business-standard completeness threshold

A hardware asset should not be treated as business-usefully documented until at least the following are known:
- asset name / location / role
- OS/platform
- CPU
- RAM
- GPU and VRAM if relevant
- storage basics
- firmware or BIOS state
- current suitability for local AI and/or coding
- known limits and preferred future use

## Hardware governance rules

1. Do not silently infer exact models.
2. Do not recommend hardware-intensive work based on unvalidated capacity.
3. Do not recommend hardware purchases before checking repurpose opportunities and firmware/driver remediation opportunities.
4. Mark unknowns explicitly.
5. Keep this process lightweight enough to maintain, but strict enough to prevent false hardware assumptions.

## Review cadence

Review and refresh the hardware registry and hardware capability document:
- after any major hardware change
- after any firmware/driver update that changes capability
- before major procurement decisions
- before major local-model/runtime changes
- before relying on a host for Apple builds, remote access, or primary inference duties

## Notes

This runbook is intended to make the hardware truth surface operational, repeatable, and safe for use by both humans and coding assistants.
