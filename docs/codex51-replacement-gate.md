
# Codex 5.1 Replacement Gate

## Purpose

This document defines the first major strategic milestone for this repository:

**The local coding system becomes capable enough to replace the level of work previously handled by Codex 5.1 for the approved bounded complex coding task classes.**

This file exists to keep implementation aligned, reduce drift, and prevent confusing wrapper/orchestration gains with genuine local-model capability gains.

This is a governing document for:

* roadmap review
* build prioritization
* qualification decisions
* promotion decisions
* local-model improvement strategy
* local-first execution policy

This document should be read together with:

* `AGENTS.md`
* `docs/version15-master-roadmap.md`
* `docs/version8-upgrade-list.md`
* `docs/level10-roadmap.md`
* `config/promotion_manifest.json`

---

# 1. Core strategic objective

The system is not considered successful merely because it has:

* a stronger manager
* better retrieval
* more traces
* more automation
* cleaner regression packs
* more lane logic

The system is successful only when the **local coding model + local orchestration stack** can repeatedly perform the target classes of work at a level that replaces the practical need for Codex 5.1 on those classes.

This means the goal is not:

* “the wrapper got better”
* “the manager rescued more failures”
* “retrieval handed over better context”
* “the guardrails prevented mistakes”

Those are important enabling mechanisms, but they are not the final measure.

The real measure is:
**How much complex coding work can the local system now complete safely, correctly, and repeatedly, with acceptable rescue/escalation rates, and with clear evidence that the local model itself is improving rather than merely being carried by the surrounding system?**

---

# 2. What “Codex 5.1 replacement” means here

## 2.1 Practical definition

For this repository, “Codex 5.1 replacement” does **not** mean universal parity with every possible coding task.

It means:
the local system can replace Codex 5.1 for a defined set of **bounded complex coding task classes** that matter to this project.

The milestone is passed when the local system can handle those task classes with:

* sustained success,
* bounded safety risk,
* acceptable escalation rates,
* reduced repeated failure recurrence,
* and evidence that first-attempt local model quality has materially improved.

## 2.2 The first target task classes

The first replacement milestone is specifically about these bounded complex coding classes:

### A. Multi-file orchestration changes

Examples:

* manager + stage integration changes
* stage/routing/manifest alignment work
* promotion and qualification control-loop changes
* adding bounded orchestration features without breaking safety semantics

### B. Retrieval + orchestration changes

Examples:

* RAG ranking or grouping changes that materially affect plan quality
* manager/retrieval interaction fixes
* grouped-target planning behavior
* lane-aware retrieval improvements

### C. Resumable / checkpointed execution work

Examples:

* Stage-8 execution checkpointing
* subplan resume/reconcile logic
* rollback-contract and state-transition work
* operationalization of resumed multi-step execution paths

### D. Safe contract handling across heterogeneous targets

Examples:

* shell/script target handling
* per-target contract generation
* grouped execution across mixed target families
* bounded rescue and refinement of literal contracts

### E. Real bounded architecture changes

Examples:

* one-subsystem-at-a-time version movement
* implementation of new stage/manager/RAG capability steps
* auditable major-version behavior changes
* nontrivial code path additions with minimal but real validation

These are the first target classes because they are exactly where reliance on Codex 5.1 became most valuable before tasks became too complex.

---

# 3. What is NOT required for this first milestone

The first replacement milestone does **not** require:

* universal coding parity
* arbitrary greenfield product builds
* unrestricted multi-repo work
* broad internet-dependent research coding
* uncontrolled shell-heavy automation
* open-ended architecture exploration with no safety bounds
* elimination of all human review

It is acceptable for the local system to still require:

* bounded human review gates
* explicit promotion/qualification checks
* manager/routing structure
* retrieval assistance
* fallback to manual handling for out-of-scope work

The milestone fails only if the target bounded complex classes are still primarily dependent on Codex 5.1-class external help.

---

# 4. Success criteria for passing the gate

## 4.1 Core pass condition

The gate is passed only if the local system shows **sustained** performance on the approved target task classes.

A one-off success is not enough.

## 4.2 Required qualitative properties

To pass, the system must demonstrate all of the following:

### A. First-attempt quality is materially improved

The local model’s first attempts must be better than earlier versions in a way that is visible in:

* fewer avoidable failures
* less manager rescue required
* fewer stale-reference / malformed prompt / obvious preflight issues
* better code-level correctness on initial execution attempts

### B. Rescue remains bounded

Manager rescue, retrieval rescue, or policy rescue may exist, but it must not dominate the outcome.

If the local model routinely fails and the manager consistently saves it, the milestone is **not** passed.

### C. Repeated-failure recurrence is reduced

Known past failure classes should be:

* prevented before launch,
* rerouted correctly,
* or otherwise reduced in recurrence.

The system must show that it is not simply re-making the same mistakes and being repaired afterward.

### D. Safety remains intact

The milestone is invalid if success comes from weakening:

* scope guards
* shell-risk protections
* literal/contract validation
* rollback semantics
* lane boundaries
* promotion/qualification discipline

### E. Operational evidence is strong

The milestone must be supported by:

* traces
* plan histories
* qualification outputs
* version-aware control-loop evidence
* clean repo state at the end of representative runs

---

# 5. Failure criteria for NOT passing the gate

The milestone must be considered **not passed** if any of the following remain true:

### A. Wrapper-only gains dominate

If most improvement comes from:

* better preflights
* more rerouting
* stronger manager rescue
* stronger retrieval packaging
  without clear model-first-attempt improvement, then the milestone is not passed.

### B. Repeated failure classes persist

If the same classes of errors keep recurring in real work, the system is not ready.

### C. Success depends on narrow canned paths

If the system succeeds only on narrowly staged or overfitted internal paths, but not on representative bounded complex tasks, the milestone is not passed.

### D. Escalation remains too high

If too many tasks still need:

* Codex/manual intervention
* repeated rescue
* manual literal synchronization
* repeated qualification/policy interpretation
  then the local system has not yet replaced the work in practice.

### E. Promotion evidence is misleading

If qualification or promotion appears favorable only because:

* failures are hidden,
* task classes are cherry-picked,
* rescue is not counted clearly,
* or comparisons are unfair,
  then the gate is not passed.

---

# 6. Model improvement vs wrapper improvement

This is the most important interpretation rule in the entire document.

## 6.1 We must not fool ourselves

The system can improve through many layers:

* manager
* retrieval
* routing
* guards
* promotion logic
* execution policy
* model behavior

These are not equivalent.

The local coding model is only improving in the strongest sense if:

* first-attempt code quality rises,
* fewer rescue actions are needed,
* less context cleanup is required,
* and more bounded complex tasks are completed correctly without intervention.

## 6.2 The attribution split

Every significant gain should be classified into one or more of:

### A. Model gain

The local coding model itself is producing better first attempts.

### B. Manager gain

The orchestrator makes better decisions, retries, splits, rescues, or reroutes.

### C. Retrieval gain

The retrieval stack presents better targets, groupings, or provenance.

### D. Guard/policy gain

The system avoids launching bad tasks or catches failures earlier.

### E. Mixed gain

A real improvement depends on multiple layers and should be credited accordingly.

## 6.3 Rule for milestone claims

A replacement claim is valid only when **model gain is materially present**.

Manager/RAG/guard gains are necessary and valuable, but they cannot by themselves justify the claim that the local coding model has reached the target replacement capability.

---

# 7. Training and learning policy

## 7.1 General rule

The local coding model should improve while the system is being built.

But we must improve it in the correct order:

1. rule hardening and guard formalization
2. trace collection and attribution
3. curated success/failure dataset construction
4. controlled training or adaptation
5. gated rollout with benchmark review

## 7.2 What should be collected

Collect and preserve:

* plan histories
* manager traces
* stage traces
* retrieval outputs and provenance
* lane/version metadata
* failure classes
* rescue/refinement lineage
* escalation outcomes
* code diff outcomes
* qualification results
* promotion decisions

## 7.3 What failures should become

Failures should be classified into:

* guard rules
* manager routing rules
* retrieval penalties or grouping exclusions
* negative examples for training
* benchmark cases for future evaluation

## 7.4 What successes should become

Successes should be classified into:

* reusable templates
* preferred contract patterns
* preferred target-grouping patterns
* positive curriculum examples
* benchmark cases for first-attempt evaluation

## 7.5 Rules-first before weights-first

Do not immediately treat every failure as a training problem.

First ask:

* should this become a rule?
* should this become a manager preflight?
* should this become a retrieval filter?
* should this become a lane-routing policy?
* should this become a qualification gate?

Only after that should it become a candidate for model-training data.

## 7.6 Training readiness rule

Do not start model-training/fine-tuning rollout until:

* attribution policy is approved
* benchmark set is approved
* curated data policy is approved
* and we can separate wrapper gains from model gains with confidence

---

# 8. Local-first execution policy

## 8.1 Core rule

The local system should do as much coding work as safely possible.

But “as much as possible” does not mean “everything immediately.”

The progression should be:

* current safe local classes
* next expandable local classes
* later high-complexity local classes
* only then true replacement-level local execution for the target benchmark

## 8.2 Local-first classes now

The local system should default to local execution for the currently safe promoted classes and bounded candidate/preview classes where the stack has proven it can execute safely.

## 8.3 Local-next classes

The next classes that should move local are:

* bounded multi-file orchestration changes
* grouped target updates with explicit contract handling
* retrieval/orchestration integration work
* resumed execution path changes
* control-loop and promotion-engine plumbing within approved bounds

## 8.4 Still out of scope for local-first by default

Until explicitly promoted:

* broad unsafe shell-control tasks
* unbounded architecture rewrites
* high-ambiguity multi-family tasks
* uncontrolled scope expansion
* model-training rollout logic without reviewed policy

## 8.5 What “more local execution” must mean

Not just more local runs.

It must mean:

* more real work executed locally,
* fewer escalations,
* fewer rescues,
* better first attempts,
* and better bounded complex task completion.

---

# 9. Recommended benchmark structure

## 9.1 Benchmark slices

The benchmark for replacement should be divided into slices:

### Slice A — first-attempt local-only

Minimal rescue, standardized retrieval context.

### Slice B — local + normal manager

Current operational system behavior.

### Slice C — local + retrieval-enriched planning

Measures stack quality with normal assistance.

### Slice D — stress/edge slice

Known difficult but still in-scope bounded complex tasks.

## 9.2 Why this is necessary

This prevents the false conclusion that:

* “the system got better”
  when really:
* only retrieval got cleaner
* or only manager rescue improved

## 9.3 Minimum benchmark evidence needed

Before declaring replacement:

* multiple tasks per target class
* repeated success, not one-offs
* clear attribution notes
* low repeated-failure recurrence
* acceptable escalation rate
* acceptable rescue rate

---

# 10. Governance and review gates

The following require explicit human review before rollout:

* benchmark set definition
* pass/fail thresholds
* training/curation policy
* model-training/fine-tuning rollout
* widening safe local-first scope materially
* promotion-policy changes that alter go/no-go behavior
* declaring the Codex 5.1 replacement milestone passed

---

# 11. Immediate build guidance

Until this gate is formally approved:

## Do next

* use `docs/version15-master-roadmap.md` as the governing build roadmap
* treat Codex 5.1 replacement as the first strategic milestone
* maximize local coding within approved safe scope
* keep attribution explicit
* continue converting repeated failures into structured memory, rules, and curated examples

## Do not do yet

* declare replacement reached
* expand scope recklessly
* start training rollout without review
* over-credit wrapper improvements as model improvements
* chase version churn without benchmark relevance

---

# 12. Review questions for humans

Before implementation proceeds against this gate, we need explicit answers to:

1. Which exact bounded complex coding tasks count as the benchmark set?
2. What rescue rate is acceptable?
3. What escalation rate is acceptable?
4. What repeated-failure recurrence rate is acceptable?
5. How much manager/RAG help is still acceptable at the gate?
6. What evidence is required to claim the local model itself improved?
7. What tasks remain explicitly out of scope for the first replacement milestone?

---

# 13. Required evidence before declaring the milestone passed

Before this gate can be marked PASS, the repo must contain reviewable evidence for:

* benchmark definitions
* pass/fail thresholds
* task-class outcomes
* trace and attribution summaries
* qualification evidence
* promotion evidence
* local-first execution share
* comparison showing the local system can now replace the target Codex 5.1-level work class

If those are missing, the milestone is not yet passed.

---

# 14. Final rule

This document is intended to stop drift.

If future implementation work does not clearly advance:

* the Codex 5.1 replacement milestone,
* Version 15 roadmap execution,
* local model capability,
* or trustworthy attribution of gains,

then that work should be considered lower priority until this gate is satisfied or revised by explicit human review.
