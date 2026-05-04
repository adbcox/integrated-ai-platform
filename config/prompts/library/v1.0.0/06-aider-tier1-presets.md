# Aider Tier 1 Presets
# Version: 1.0.0
# Effective: 2026-05-04
# Derivation: D-17-95 (work-routing enforcement)

## Purpose

Pre-canned `scripts/aider-task.sh` invocation templates for the most
common TIER 1 patterns. Copy-paste the matching template, substitute
`<TARGET>` and `<FILE>`, and run.

Classifier reference: `docs/architecture-facts/work-routing-doctrine.md`

**ROUTING PRE-CHECK (D-17-95):**
Before dispatching to Claude Code or Codex, classify the task:
- TIER 1 (Aider-eligible): ≤5 files, no runtime probes, no API/Vault/Docker, deterministic diff.
  If TIER 1: decline execution, surface back with the exact `scripts/aider-task.sh` invocation below.
- TIER 2 (Claude Code/Codex): proceed if orchestration, probes, Vault, or judgment required.
- TIER 3 (frontier): surface to operator for manual decision.

---

## Preset: drift-fix

**When:** A specific word, phrase, or constant is wrong/stale in a doc or source file.
The correct value is known without running anything.

```bash
scripts/aider-task.sh --class C0 \
  "Replace '<OLD_VALUE>' with '<NEW_VALUE>' everywhere in this file" \
  <FILE>
```

**Example — fix stale hostname in doctrine:**
```bash
scripts/aider-task.sh --class C0 \
  "Replace 'mac-mini.lan' with 'mac-mini.internal' everywhere in this file" \
  docs/architecture-facts/opnsense-dns-authority.md
```

**Example — fix stale model name in config:**
```bash
scripts/aider-task.sh --class C0 \
  "Replace 'qwen2.5-coder:1.5b' with 'qwen2.5-coder:7b' everywhere in this file" \
  domains/router.py
```

---

## Preset: header-annotation

**When:** A file needs a standard header comment, version block, or `# Derivation:` line added.

```bash
scripts/aider-task.sh --class C0 \
  "Add a file-level header comment block at the top with: description, date, and originating deliverable <D-NN-NN>" \
  <FILE>
```

**Example:**
```bash
scripts/aider-task.sh --class C0 \
  "Add a header comment at the top: '# Work-routing classifier helper. D-17-95. 2026-05-04.'" \
  scripts/aider-task.sh
```

---

## Preset: docstring-add

**When:** A function, class, or script is missing a docstring or top-level usage comment.

```bash
scripts/aider-task.sh --class C0 \
  "Add a one-line docstring to the <FUNCTION_NAME> function describing what it does" \
  <FILE>
```

**Example:**
```bash
scripts/aider-task.sh --class C0 \
  "Add a one-line docstring to the classify function describing its routing logic" \
  domains/router.py
```

For multi-function files, be specific:
```bash
scripts/aider-task.sh --class C0 \
  "Add one-line docstrings to all public methods that currently have none" \
  domains/learning.py
```

---

## Preset: type-hint-add

**When:** A function signature is missing type annotations and the types are
inferrable from the code (no runtime inspection needed).

```bash
scripts/aider-task.sh --class C0 \
  "Add type hints to all function signatures in this file that currently lack them" \
  <FILE>
```

**Example:**
```bash
scripts/aider-task.sh --class C0 \
  "Add type hints to all function signatures in this file that currently lack them" \
  domains/router.py
```

---

## Preset: refactor

**When:** A function, block, or module needs internal restructuring without
changing external interface or behavior. No runtime validation needed to verify.

```bash
scripts/aider-task.sh --class C1 \
  "Refactor <DESCRIPTION> — do not change the external interface or return types" \
  <FILE1> [<FILE2>]
```

**Example — extract helper:**
```bash
scripts/aider-task.sh --class C1 \
  "Extract the model selection logic from classify() into a private _select_model() helper without changing the classify() interface" \
  domains/router.py
```

**Example — rename for clarity:**
```bash
scripts/aider-task.sh --class C0 \
  "Rename the variable 'r' to 'route' throughout this file for clarity" \
  domains/router.py
```

---

## Tier 2 boundary note

Multi-paragraph doc-authoring is not Tier 1. Route to Claude Code/Codex:

- doctrine extensions
- chronicle/finding appends to existing long docs
- net-new runbook/ADR/doc authoring

Aider should refuse these and surface back with a Tier 2 routing note.

## Preset: cap-drop-add

**When:** A docker-compose service stanza is missing `cap_drop: [ALL]` and/or
`security_opt: [no-new-privileges:true]` per the Container Hardening doctrine.

```bash
scripts/aider-task.sh --class C0 \
  "Add 'cap_drop: [ALL]' and 'security_opt: [no-new-privileges:true]' to the <SERVICE_NAME> service stanza" \
  <COMPOSE_FILE>
```

**Example:**
```bash
scripts/aider-task.sh --class C0 \
  "Add 'cap_drop: [ALL]' and 'security_opt: [no-new-privileges:true]' to the scraparr service stanza" \
  docker/arr-stack/docker-compose.yml
```

---

## When NOT to use these presets (escalate to Claude Code)

- The "correct value" requires reading a live config, running a command, or checking a service state → TIER 2
- The doc to update needs judgment about what the right policy should be → TIER 2
- The task is multi-paragraph doc authoring, chronicle append, or doctrine extension → TIER 2
- The refactor changes external interface or callers need updating across > 5 files → TIER 2
- The new doc requires interviewing live platform state (running containers, Vault secrets, DNS records) → TIER 2
- The task is an audit, review, or architecture decision → TIER 2 or TIER 3

See: `docs/architecture-facts/work-routing-doctrine.md`
