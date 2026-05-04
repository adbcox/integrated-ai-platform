# Hand-grade packet 05 — T3-A long-context lc-short-gemma-friendly

**Run:** 20260503T180613Z
**Model:** gemma2:27b on mac-studio
**Workload:** long-context
**Task ID:** lc-short-gemma-friendly

## Auto-grader output

- score: **0.75**
- pass: **True**
- notes: 3/4 expected facts present
- wall_s: 41.732054833, tps: 23.980491589070905

## Task summary

7K variant — Finding T recall (Gemma 8K-context fairness)

## Model response (full)

```
Finding T highlights the lack of a **coherent inventory and visualization layer for the platform's operational state**. This includes:

* **OS/Firmware versions:** Tracking macOS, firmware on all hardware components (motherboard BIOS, GPU VBIOS, NVMe drives, network cards), accessory device firmware.
* **Container runtime:** Docker version, container images used, their provenance and security scans.
* **Application binaries:** Versions of all software running on the platform.
* **Library dependencies:** Tracking which libraries are used by each application and their versions.

The canonical example is the 2026-05-02 macOS upgrade (26.3 → 26.4.1) on the Mac Mini orchestration node. The AI recommended this upgrade without consulting:

* **Asset state:** Which node was appropriate for the upgrade (orchestration vs idle compute).
* **Premise against literature:** RDMA major-vs-minor version requirement for distributed training.
* **Operational dependencies:** Impact of the upgrade on the running orchestration services.

The operator caught the planning failure, but the reboot was already triggered. This incident demonstrates the need for a platform operational substrate that can answer these questions and prevent such failures in the future.
```

## Operator scoring

- [ ] coherent? (yes / no)
- [ ] addresses task? (yes / partial / no)
- [ ] ship-ready quality? (yes / no)
- [ ] auto-grade fair? (yes / too-low / too-high) — by how much?
- [ ] hand-grade 0.00-1.00: ___
- [ ] notes:
