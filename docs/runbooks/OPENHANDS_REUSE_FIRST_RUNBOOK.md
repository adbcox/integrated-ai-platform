# OpenHands Reuse-First Runbook

## Scope
Operational runbook for the current OpenHands reuse-first implementation in this repository.

## 1) Install / prerequisites
Run from repo root:

```sh
bin/oss_wave_openhands.sh prereqs
```

Expected:
- `PASS: docker is available`

Ensure config exists and is locked:

```sh
cat config/oss_wave/openhands.env
```

Expected key fields:
- `LLM_MODEL=qwen2.5-coder:14b` (or `qwen2.5-coder:7b` if operator intentionally downgrades)
- `LLM_BASE_URL=http://host.docker.internal:11434/v1`
- `LLM_API_KEY=ollama-placeholder`
- `OPENHANDS_RUNTIME_IMAGE=docker.openhands.dev/openhands/runtime:0.59-nikolaik`

## 2) Launch commands
Validate config:

```sh
bin/oss_wave_openhands.sh validate-config
```

Headless launch (task can be overridden):

```sh
OPENHANDS_TASK="Create /workspace/tmp/openhands_manual.txt with content MANUAL_OK" \
  bin/oss_wave_openhands.sh launch-headless
```

GUI launch:

```sh
bin/oss_wave_openhands.sh launch-gui
```

## 3) Validation command (required)
Use the canonical validation script:

```sh
python3 bin/oss_wave_openhands_validate.py
```

What it does:
- runs headless OpenHands task
- captures logs to `artifacts/oss_wave/openhands_validation.log`
- requires `AgentState.FINISHED` in logs
- fails on timeout or missing finished state

Expected success output:
- `PASS: OpenHands validation observed AgentState.FINISHED`

## 4) Expected outputs
After a successful validation run:
- log file exists: `artifacts/oss_wave/openhands_validation.log`
- log contains `AgentState.FINISHED`
- wrapper exits zero

## 5) Known failure modes and operator action
### A) Stuck loop
Symptoms:
- repetitive planning/tool loop, no completion
- no `AgentState.FINISHED`

Actions:
1. lower task scope and rerun validation
2. switch model from 14b to 7b or reverse in `config/oss_wave/openhands.env`
3. verify Ollama responsiveness separately

### B) Timeout
Symptoms:
- validator exits with timeout (`124`)

Actions:
1. rerun with larger timeout (for local resource pressure):
   `python3 bin/oss_wave_openhands_validate.py --timeout-seconds 900`
2. inspect `artifacts/oss_wave/openhands_validation.log`
3. reduce prompt complexity and rerun

### C) Bad model behavior
Symptoms:
- hallucinatory edits, repeated incorrect actions, unstable completion

Actions:
1. keep wrapper/policy unchanged (no architecture drift)
2. switch `LLM_MODEL` between approved `qwen2.5-coder:7b` and `:14b`
3. rerun canonical validator and require `AgentState.FINISHED`

## 6) Rollback / disable
Disable OpenHands env posture:

```sh
bin/oss_wave_openhands.sh rollback
```

This removes `config/oss_wave/openhands.env`; wrapper remains present but inactive without env.
