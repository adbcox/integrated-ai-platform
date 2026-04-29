# ADR-A-012 — Equivalence harness doctrine for source-of-truth migrations

**Status:** Accepted
**Date:** 2026-04-29
**Source:** Block 4.C C5.2 / Discovery #17, Phase 13 Increment 1 D-OP

## Context

Block 4.C migrated the platform's service inventory from a homegrown
YAML file (`config/service-registry.yaml`) to NetBox's CMDB
(`netbox.internal`). The migration shipped in C3 and was proven
correct in C5.2 by running both the old and new sources through the
existing consumer (`scripts/validate-cmdb.sh`) and diffing the
outputs.

The first equivalence probe revealed three lossy collapses
(Discovery #17): `health_expect` lists collapsed to first value;
`port` vs `internal_port` distinction lost; one cosmetic `'open'`
sentinel coerced to `0`. Each was visible at *migration time* — C3
explicitly chose those collapses — but became a problem only at
*deprecation time* when the equivalence gate required byte-identity.

The C3 spec called the collapses "deliberate." That framing is the
trap: a deliberate collapse at migration time becomes an undocumented
behavioural regression at deprecation time. The collapse was always
going to fail equivalence; it just deferred the failure to a
later gate.

The fix in C5.2 was to extend NetBox's schema with two new custom
fields (`health_expect_extra`, `port_is_internal`), backfill them,
and update the loader to round-trip the registry view from NetBox
without behavioural drift. This was recoverable but expensive: an
extra audit, an extra schema migration, and an extra regression
window — all inside C5.2's gate, instead of inside C3's.

The pattern generalises. Every future source-of-truth migration
(InvenTree replacing component spreadsheets, Headscale replacing
Tailscale, hypothetical Phase 14 storage abstraction) has the same
shape: source A → target B, with consumer X reading whichever is
canonical. If A and B don't round-trip exactly through X, the
deprecation of A is a behavioural regression dressed up as a
cleanup.

## Decision

Every source-of-truth migration must include an equivalence harness
that runs at **migration time**, not just at deprecation time.

### Required artefacts

1. **`--verify-roundtrip` mode on the migration script.** The
   script that copies A → B must also support a mode that:
   - loads the source (A),
   - reads the target (B),
   - runs the consumer (X) against both,
   - normalises and diffs the consumer's output,
   - exits non-zero if the diff is non-empty.

   The diff must be **byte-identical** after a defined normalisation
   step (header lines that legitimately differ, e.g., the source
   name in a status banner, can be stripped; semantic content
   cannot).

2. **Raw harness output captured in evidence.** The closeout doc
   for the migration block must include the raw output of the
   `--verify-roundtrip` run, not a paraphrase. SHA256 prefix of
   the normalised output (both sides) is acceptable evidence; a
   summary like "verified equivalent" is not.

3. **Lossy fields explicitly enumerated.** If any field in A
   cannot round-trip through B, the migration script must emit
   a `LOSSY` diagnostic naming the field, and the closeout must
   either:
   - extend B's schema to capture the lost dimension and re-run
     the harness; or
   - declare the field "irreversible by design" with an explicit
     operator sign-off recorded in the closeout.

   Silent collapse is forbidden.

4. **Deprecation gate consumes the harness output.** When A is
   later deprecated (e.g., file marked `*.DEPRECATED`, stack flag
   flipped from `yaml` to `netbox`), the deprecation closeout
   must include a re-run of the harness showing equivalence still
   holds. The deprecation gate doesn't re-discover lossiness; it
   verifies that the migration-time harness still passes.

### Worked example: Block 4.C C5.2

C3 migrated `service-registry.yaml` → NetBox custom fields.
**C3 did not run a `--verify-roundtrip` probe.** Three lossy
collapses landed silently.

C5.2a *did* run an equivalence probe (per this ADR's intent,
applied retroactively). The probe surfaced the three losses
exactly. Resolution: extend NetBox schema (C5.2b/c), re-run the
harness, achieve byte-identical equivalence. Closeout
(`PHASE_13_BLOCK_4C_CLOSEOUT_2026-04-29.md`) captures the
SHA256 prefix `2d4a8fd21589de80...` of the normalised output
on both sides plus the diff exit code (0).

If C3 had run the harness, the schema extension would have
landed in C3, not C5.2. C5.2 would have been a clean
deprecation. The pattern in this ADR is what C3 should have
followed and what every future source-of-truth migration will.

### What "consumer" means

The "consumer" in the harness is the load-bearing read of A or
B that the operator-facing tooling depends on. For the C5.2
case, that was `scripts/validate-cmdb.sh`. For an InvenTree
migration, it would be whatever queries the part inventory
(BoM exports, supplier-quote scripts, vision-recognition
plugin). The harness uses that real consumer, not a synthetic
diff of the source files — because the bug class is "the
consumer behaves differently against B than against A," not
"B isn't bit-identical to A."

If the migration has multiple consumers, the harness runs each
one. Equivalence holds only if every consumer round-trips.

## Consequences

- Every block in Phase 13 onward that migrates an authoritative
  data source must implement `--verify-roundtrip` in the
  migration script as a first-class deliverable, not an
  afterthought.
- The canonical add-new-service pattern
  (`docs/runbooks/add-new-service.md`) does not need this
  doctrine — it adds new state, doesn't migrate. But any block
  that *replaces* an existing source with a new one (4.E
  joining cross-index data, 4.J writing to NetBox dcim if it
  replaces an existing observation feed, HF-1 replacing any
  prior fitness store) does.
- The harness output format is unstandardised today. A future
  block may converge on a shared `bin/equivalence_probe.py`
  helper; for now, each migration's script implements its own
  `--verify-roundtrip` mode following the contract above.
- Deprecation gates for migrations carry an extra step (re-run
  the harness). This is cheap (the harness is automated) and
  buys ironclad evidence that the cleanup did not regress
  consumer behaviour.

## Lessons that motivated this doctrine

1. "Deliberate" collapses at migration time still surface as
   behavioural regressions at deprecation time. The deferral
   doesn't reduce the regression's likelihood, only its
   timeliness.
2. Schema-level diff (does A and B have the same fields?) is
   weaker than consumer-level diff (does the consumer behave
   the same?). A consumer can mask a schema mismatch via
   defaults, fall-throughs, or implicit coercions, all of which
   are silent until the wrong path is exercised.
3. The harness pays for itself the first time it catches a
   loss. The C5.2 case was caught at the equivalence probe; it
   would have been a multi-day post-deprecation
   debugging session if it had escaped.
