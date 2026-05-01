# Observed Architecture Patterns

Patterns surfaced during the 2026-04-30→05-01 article-intake window
(deliverable 17.S). Recorded here as observed-in-the-wild patterns
worth knowing about — not endorsements, not roadmap commitments.

When a pattern matures into adoption, it gets a proper deliverable
under the appropriate phase. This file is a thinking aid, not a
queue.

---

## Symphony — explicit-orchestration agent pattern

**Pattern.** A coordinator process holds the canonical task graph
and explicitly dispatches sub-agents per node. Each sub-agent
receives only the inputs it needs, returns only its declared
outputs, and never side-channels other sub-agents. The coordinator
is the only thing that knows the global plan.

**Why it matters here.** The platform's existing autonomy work
(decomposer → implementer → reviewer chain in `~/.claude/agents/`)
already follows this shape implicitly. Symphony makes the
"coordinator owns the graph" property *enforced* rather than
emergent — sub-agents can't accidentally grow lateral coupling.

**When to consider.** If the agent-surface audit (17.F) finds
multiple agents with overlapping concerns or unclear boundaries,
the Symphony pattern is one resolution: collapse the overlap into
a coordinator and explicit children. Don't apply pre-emptively;
wait for 17.F evidence.

**Watch-out.** Coordinator becomes a bottleneck and a single point
of failure. Worth it when the alternative is uncoordinated
sub-agents stepping on each other; not worth it when sub-agents
are genuinely independent.

---

## Spec Kit — spec-as-source-of-truth for feature work

**Pattern.** Every non-trivial feature starts as a written spec
(intent, acceptance criteria, out-of-scope, examples). Code is
generated/written *against* the spec; tests are derived from the
spec; PR review is "does this match the spec." The spec lives in
the repo next to the code and is updated when behavior changes.

**Why it matters here.** The platform already does this informally
(deliverable prompts, phase plans, ADRs). Spec Kit formalizes the
deliverable-prompt step into a repo artifact rather than a chat
turn — which means it survives compaction, can be cited from
commits, and can be mechanically diffed when behavior changes.

**When to consider.** If 17.B's capability audit template proves
load-bearing across several deliverables, the natural next step is
"every deliverable produces a spec artifact, not just a prompt."
That's Spec Kit. Don't introduce it as a separate tool — fold it
into the deliverable-prompt convention.

**Watch-out.** Spec rot: spec and code diverge silently. Mitigated
by making the spec the test source rather than a parallel doc.

---

## OpenShell — self-describing service shells

**Pattern.** Each service exposes a structured "what am I, what do
I depend on, what do I expose" endpoint (typically `/.well-known/`
or similar). A central index walks all services on a schedule and
materializes the topology — no hand-maintained CMDB rows for
service-to-service edges.

**Why it matters here.** xindex (Phase 16 D-16-02) is the platform's
incumbent answer for cross-service indexing, but it currently
ingests from configured sources (NetBox, Plane, framework docs) —
not from the services themselves. OpenShell would invert that:
services declare themselves; xindex collects.

**When to consider.** If the topology-api audit (17.G) and the
agent-surface audit (17.F) both find significant configuration
drift between declared (NetBox) and actual (running) state,
OpenShell-style self-declaration is one resolution. Probably worth
prototyping on a single service first (candidate: a service we'd
otherwise need to retire) before any platform-wide commitment.

**Watch-out.** Adds a runtime dependency to every service
(/.well-known endpoint must work or the service is invisible to
the index). Configuration drift moves from "NetBox lies" to
"service lies" — different failure mode, not necessarily a better
one. Decide based on which lie is easier to detect.

---

## ESP32 enclosure license tracking — provenance for fabricated parts

**Pattern (consider when expanding Block 3-style builds).** When
fabricating physical hardware (ESP32-based sensors, label-printer
adapters, anything 3D-printed or PCB-ordered), record the license
of every external design input used: STL files, KiCad libraries,
firmware snippets, schematic references. Treat hardware design
provenance with the same rigor as software dependencies.

**Why it matters here.** Block 3 (MacBook Pro M5 parity) and any
future hardware fabrication work would benefit from this if
designs are sourced externally. Phase 13 Block 3 builds were
historical and don't need retroactive tracking, but if Block 3-
style hardware fabrication recurs (custom enclosures, sensor
mounts, peripheral adapters), the license-tracking discipline
should travel with it.

**When to consider.** Before any deliverable that involves
fabricating physical hardware from external designs. The discipline
is the SPDX-ID-per-file convention applied to STL/KiCad/firmware
inputs, indexed in a manifest committed alongside the build files.

**Watch-out.** Manyfold + Gitea LFS schema work (deferred — see
Phase 18 narrative) is the natural home for this metadata if/when
a 3D model database deliverable is scoped. Until then, file the
license-ID inline in the build's README is sufficient.
