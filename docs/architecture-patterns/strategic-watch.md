# Strategic Watch

External developments that could affect platform direction without
being immediate action items. Recorded so future-self knows the
context if/when these mature into something requiring response.

Surfaced during the 2026-04-30→05-01 article-intake window
(deliverable D-17-19).

---

## Thingiverse direction — community 3D-model commons under strain

**Signal.** The largest community repository for 3D-printable
designs has been showing signs of platform-direction risk:
licensing ambiguity on uploaded models, unclear long-term
ownership, periodic policy churn. Community has been forking to
alternatives (Printables, Thangs, MakerWorld) but no clear
successor with the same breadth.

**Why it matters here.** Any future 3D-model database deliverable
(see Phase 18 narrative — Manyfold + Gitea LFS schema) needs to
consider where source models come from. If Thingiverse remains the
default index, license-cleanliness becomes harder to verify per
model. If a successor consolidates the commons, the schema needs
to handle multi-source provenance from day one.

**Mitigations to keep in mind.**
- Schema should record source URL + retrieval date alongside
  SPDX license ID, not just the license. Provenance lets us
  re-verify if the upstream platform changes terms.
- Prefer models with permissive licenses (CC-BY-SA-4.0, CERN-OHL-S)
  to forestall downstream redistribution friction.
- Don't build the schema around any single source's API;
  ingestion should be source-agnostic.

**Action threshold.** No action until a 3D-model database
deliverable is scoped. When it is, revisit this entry first.

---
