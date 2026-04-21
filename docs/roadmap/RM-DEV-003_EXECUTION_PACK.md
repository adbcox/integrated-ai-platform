# RM-DEV-003 — Execution Pack

## Title

**RM-DEV-003 — Bounded autonomous code generation**

## Canonical relationship

- Master roadmap authority: `docs/roadmap/ROADMAP_MASTER.md`
- Normalized backlog entry: `docs/roadmap/ROADMAP_INDEX.md`
- High-priority implementation guide: `docs/roadmap/HIGH_PRIORITY_IMPLEMENTATION_GUIDE.md`
- Related primary item: `RM-DEV-005`

## Objective

Enable the system to autonomously execute safe, bounded coding work with explicit scope, validation, artifact, and rollback rules.

This item is a direct downstream execution capability of the local-development-assistant program and should be built on top of the same runtime, model-routing, artifact, and evaluation substrate used by `RM-DEV-005`.

## Why this matters

This is the item that turns a stronger local development assistant into an actually usable coding operator.

Without bounded autonomous code generation, local-model improvement remains mostly advisory. With it, the system can:

- execute narrow safe coding slices without constant human orchestration,
- preserve evidence and rollback posture,
- reduce routine dependence on external paid coding agents,
- and move more work into the local-first operating model.

## Required outcome

The system must be able to accept a bounded coding task and produce:

- a validated patch or explicit no-op,
- machine-readable artifact outputs,
- ordered validation results,
- rollback guidance,
- and a clear ready / follow-up / rollback recommendation.

## Non-goals

This item is **not** permission for unbounded repo rewrites.

Do not use this item to justify:

- broad redesigns across the repo,
- uncontrolled multi-file changes with no explicit scope,
- hidden environment mutation,
- destructive actions without explicit contract and rollback path,
- or replacing all review/evaluation logic with model intuition.

## Adopt-first software and patterns

### Ollama
- Role: local inference host and API surface
- Official docs: https://docs.ollama.com/
- Relevant docs:
  - Quickstart: https://docs.ollama.com/quickstart
  - API intro: https://docs.ollama.com/api
  - Usage metrics: https://docs.ollama.com/api/usage
  - Modelfile reference: https://docs.ollama.com/modelfile

#### Why it is relevant here
Bounded autonomous code generation needs a predictable local model-serving layer, stable API, and measurable usage/latency counters. Ollama exposes a local API by default and returns usage metrics like total duration, prompt eval counts, and eval counts, which are useful for execution telemetry and benchmark comparison. citeturn280140search0turn280140search3

### Aider
- Role: repo-aware edit adapter
- Repo map docs: https://aider.chat/docs/repomap.html

#### Why it is relevant here
Aider’s repository map provides concise whole-repo symbol context, which is useful for bounded edits that need to respect existing abstractions. For `RM-DEV-003`, that means Aider is a strong candidate edit primitive, but only inside the governed runtime and never as the system backbone. citeturn280140search4

### MCP
- Role: protocol boundary for tools/resources/prompts
- Official spec: https://modelcontextprotocol.io/specification/

#### Why it is relevant here
MCP defines a JSON-RPC based protocol with lifecycle management and server features for tools, resources, and prompts. It is the correct boundary for exposing execution tools, repository context, and helper prompts without inventing ad hoc connectors. citeturn280140search10turn280140search11

### SWE-bench
- Role: benchmark and evaluation reference
- Overview: https://www.swebench.com/SWE-bench/
- FAQ: https://www.swebench.com/SWE-bench/faq/

#### Why it is relevant here
SWE-bench provides real-world GitHub issues with reproducible evaluation, including Docker-based harnessing and verified subsets. This should inform the benchmark and quality gate design for autonomous coding performance. citeturn280140search2turn280140search7

### gVisor
- Role: isolation for risky or untrusted execution
- Docs: https://gvisor.dev/docs

#### Why it is relevant here
gVisor provides a strong isolation layer and includes an OCI runtime (`runsc`). It should be used as defense-in-depth for higher-risk execution classes rather than assuming all local execution is equally safe. citeturn957525search2

### OpenHands Software Agent SDK
- Role: pattern source for agent/runtime/tool/workspace design
- Repo: https://github.com/OpenHands/software-agent-sdk
- SDK docs: https://docs.all-hands.dev/sdk
- Local runtime caution: https://docs.all-hands.dev/openhands/usage/runtimes/local

#### Why it is relevant here
OpenHands SDK provides composable agent, tool, and workspace patterns, and supports either local-machine workspaces or ephemeral workspaces. Its local runtime docs explicitly warn that local runtime has no sandbox isolation and should be used only in controlled environments. Use it for patterns and possible future components, but keep security posture explicit. citeturn432185search1turn432185search3turn432185search0

## Recommended architecture posture

### Core rule
`RM-DEV-003` must sit on top of the runtime hardened by `RM-DEV-005`.

### Preferred flow
1. task intake with explicit scope and allowed files
2. repo/context prep
3. model selection and profile pinning
4. bounded edit execution
5. ordered validations
6. artifact emission
7. promote / follow-up / rollback decision

### Required boundaries
- bounded file list
- explicit objective
- validation order
- rollback rule
- artifact outputs
- forbidden file families
- escalation trigger

## Mandatory contracts

Every execution slice under `RM-DEV-003` must specify:

- **Objective**
- **Allowed files**
- **Forbidden files**
- **Expected file posture** (append-only/helper/narrow mutation/etc.)
- **Validation sequence**
- **Rollback rule**
- **Artifact outputs**
- **Promotion decision rule**

## Required artifacts

Every autonomous coding run should emit at least:

- task descriptor
- selected model and profile
- repo/context inputs
- changed files list
- patch or no-op output
- validation results in order
- execution status
- rollback guidance
- follow-up recommendation
- timing/usage metadata where available

## Suggested artifact paths

- `artifacts/autocode/<task_id>/task.json`
- `artifacts/autocode/<task_id>/execution.json`
- `artifacts/autocode/<task_id>/validation.json`
- `artifacts/autocode/<task_id>/summary.md`

## Validation policy

### Ordered validation sequence
1. syntax / lint / changed-file-local checks
2. task-specific unit or narrow integration checks
3. broader quick checks where appropriate
4. benchmark/evidence update if the task belongs to a measured class

### Validation rule
Do not claim success based only on generated diff text. Validate changed-on-disk results.

## Benchmark and evidence posture

### Key metrics
- first-attempt success rate
- retry count
- rescue/manual escalation rate
- repeated-failure recurrence rate
- validation pass rate
- rollback-needed rate

### Evidence rule
Claim improvement only when fixed benchmark cohorts improve. Avoid conflating wrapper heuristics with true model or system capability gains.

## Immediate implementation sequence

### Phase 1 — bounded task contract layer
Build the task-spec format and enforce required fields.

### Phase 2 — governed edit path
Connect model routing + repo prep + edit adapter inside the runtime.

### Phase 3 — validation and artifact closure
Require machine-readable outputs and ordered validation execution.

### Phase 4 — measured autonomy promotion
Promote safe task classes to autonomous execution only when evidence supports it.

## Best practices
- keep tasks narrow and additive-first
- pin model profiles per task class
- prefer repo-aware context over whole-file dumping
- use sandbox/isolation for risky execution classes
- store failures as reusable memory, not just logs
- keep human review in the loop for broader or ambiguous tasks

## Common failure modes
- vague objective with no task anchor
- too many editable files for the selected task class
- no rollback rule
- no changed-on-disk validation
- ad hoc adapter use outside the runtime
- success claims based on anecdotal wins instead of measured cohorts

## Execution handoff template

When pulling this item for execution, the handoff should include:

- roadmap ID: `RM-DEV-003`
- related items: `RM-DEV-005`, `RM-DEV-002`
- exact objective
- allowed files
- forbidden files
- expected file posture
- model/profile choice
- validation sequence
- artifact outputs
- rollback rule
- escalation rule

## Recommended first milestone

Implement the bounded task contract and artifact-complete execution envelope first, before broadening autonomous scope.

That first milestone should prove the system can safely complete narrow tasks end to end with explicit evidence.
