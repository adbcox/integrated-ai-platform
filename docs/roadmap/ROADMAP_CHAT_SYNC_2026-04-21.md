# Roadmap Chat Sync — 2026-04-21

This document records the roadmap items normalized from the roadmap-intake chat and synced into the canonical roadmap system in `docs/roadmap/`.

## Purpose

This file prevents roadmap items captured in chat from existing only in conversation history.
It also records the canonical IDs chosen for the synced items and the intended relationship between the new canonical `docs/roadmap/` tree and the older top-level `roadmap/` tree.

## Canonicality decision

- **Canonical roadmap root:** `docs/roadmap/`
- **Legacy roadmap root:** `roadmap/`
- **Rule:** new roadmap items must be added under `docs/roadmap/` only.
- **Legacy treatment:** the top-level `roadmap/` tree should be treated as historical planning storage unless and until it is migrated.

## Synced roadmap items

### RM-DEV-005
- **Title:** Local autonomy uplift, OSS intake, and Aider reliability hardening
- **Category:** DEV
- **Type:** Program
- **Status:** Proposed
- **Priority:** Critical
- **LOE:** XXL
- **Strategic value:** 5
- **Architecture fit:** 5
- **Execution risk:** 3
- **Dependency burden:** 5
- **Readiness:** near

#### Description
Continuously improve the local coding stack so the integrated AI platform becomes more capable of handling routine coding and adjacent development tasks without paid external agents being required for normal work.

#### Why it matters
This is the primary force-multiplier item for the home developer assistant. It directly improves Ollama-first execution quality, Aider reliability, local autonomy, artifact quality, and long-term independence from Claude Code and Codex.

#### Key requirements
- introduce a disciplined OSS intake and shortlist-evaluation workflow
- harden the inference gateway, model profiles, workspace, and artifact paths for local execution
- keep Aider inside the canonical runtime as an adapter rather than a parallel backbone
- add prompt packs, failure memory, repo-pattern memory, critique injection, and benchmark-driven routing
- track local-autonomy metrics and burn down external-model dependence over time

#### Affected systems
- local inference and model routing
- developer assistant runtime
- Aider adapter path
- artifact and validation stack
- autonomy metrics and evaluation
- OSS adoption review workflow

#### Expected file families
- runtime / gateway docs and configs
- roadmap / package and evaluation docs
- benchmark and artifact schemas
- adapter integration docs
- autonomy scorecard and reporting surfaces

#### Dependencies
- lower-phase runtime hardening
- canonical artifact and validation path
- benchmark/evaluation surfaces
- shared runtime contracts

#### Grouping candidates
- `RM-DEV-002`
- `RM-DEV-003`
- `RM-INTEL-001`

#### Recommended first milestone
Lock the adoption shortlist, establish the current local-autonomy scorecard baseline, and produce the first bounded execution slice for inference-gateway/profile hardening and Aider adapter reliability.

#### Pull-first rule
`RM-DEV-005` is the current pull-first roadmap item and should be preferred over new domain-expansion work unless lower-phase prerequisites are the actual blocker.

---

### RM-DOCAPP-002
- **Title:** AI-assisted website generation, SEO, and analytics delivery stack
- **Category:** DOCAPP
- **Type:** Program
- **Status:** Proposed
- **Priority:** High
- **LOE:** XL
- **Strategic value:** 4
- **Architecture fit:** 4
- **Execution risk:** 2
- **Dependency burden:** 3
- **Readiness:** later

#### Description
Add a website-delivery capability that uses adopted OSS tools to generate editable, deployable websites with SEO and analytics support rather than building a custom web-design platform from scratch.

#### Key requirements
- OSS-backed website generation workspace
- post-generation SEO and discoverability workflow
- analytics instrumentation path
- reusable vertical template packs for service businesses and vendors

---

### RM-SHOP-002
- **Title:** 3D capture, guided measurement, and reconstruction stack
- **Category:** SHOP
- **Type:** Program
- **Status:** Proposed
- **Priority:** High
- **LOE:** XL
- **Strategic value:** 4
- **Architecture fit:** 4
- **Execution risk:** 3
- **Dependency burden:** 3
- **Readiness:** later

#### Description
Add a 3D workflow that guides photo capture for measurement tasks, supports room-scale spatial estimation, integrates with the purchased 3D scanner, and enables photo-based reconstruction of smaller objects and parts.

---

### RM-SHOP-003
- **Title:** 3D model inventory, reuse, and external sourcing library
- **Category:** SHOP
- **Type:** System
- **Status:** Proposed
- **Priority:** High
- **LOE:** XL
- **Strategic value:** 4
- **Architecture fit:** 4
- **Execution risk:** 2
- **Dependency burden:** 3
- **Readiness:** later

#### Description
Inventory local 3D models, attach semantic metadata, support whole-model and partial-geometry reuse, and search trusted external model repositories so future design work does not restart from zero.

---

### RM-SHOP-004
- **Title:** Outdoor structure concept design and architect handoff
- **Category:** SHOP
- **Type:** Enhancement
- **Status:** Proposed
- **Priority:** High
- **LOE:** L
- **Strategic value:** 3
- **Architecture fit:** 4
- **Execution risk:** 2
- **Dependency burden:** 2
- **Readiness:** later

#### Description
Extend the woodworking/design capability so the system can generate outdoor-structure concept packages for fences, boat docks, and similar builds using adopted OSS design tools, producing architect-readable handoff material rather than final engineered packages.

---

### RM-INV-003
- **Title:** Live product search, pricing history, and inventory-aware procurement workflow
- **Category:** INV
- **Type:** System
- **Status:** Proposed
- **Priority:** High
- **LOE:** L
- **Strategic value:** 4
- **Architecture fit:** 4
- **Execution risk:** 2
- **Dependency burden:** 3
- **Readiness:** later

#### Description
Support real product discovery with live listings, in-stock verification, historical pricing context, watchlists, and future linkage to owned hardware and procurement needs.

---

### RM-MEDIA-003
- **Title:** Media inventory hygiene, duplicate detection, and cleanup advisory
- **Category:** MEDIA
- **Type:** Enhancement
- **Status:** Proposed
- **Priority:** Medium
- **LOE:** M
- **Strategic value:** 3
- **Architecture fit:** 5
- **Execution risk:** 1
- **Dependency burden:** 2
- **Readiness:** later

#### Description
Extend the media-control branch so the system can identify likely duplicate TV and movie files, flag conservative cleanup candidates, and generate approval-based cleanup recommendations.

---

### RM-MEDIA-004
- **Title:** Media stack configuration optimization and sports-event acquisition
- **Category:** MEDIA
- **Type:** Enhancement
- **Status:** Proposed
- **Priority:** High
- **LOE:** M
- **Strategic value:** 3
- **Architecture fit:** 5
- **Execution risk:** 2
- **Dependency burden:** 2
- **Readiness:** later

#### Description
Extend the media-control branch so the system can optimize Sonarr, Radarr, and Plex configuration and add sports-event acquisition and normalization support, with Formula One and Sportarr-style workflows as the initial target.

## Sync notes

- These entries were normalized from chat and inserted into the canonical roadmap system.
- The root index now contains the stable item IDs and titles.
- This sync file carries the detail needed so these items are not preserved only in chat.
- Future execution artifacts should reference the assigned roadmap IDs directly.
