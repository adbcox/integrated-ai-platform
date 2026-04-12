# Local-First Task Intake

This is the first-pass front door for task execution. It routes tasks using local rules and only packetizes Codex escalation when escalation is selected.

## What it does
- accepts task name + goal
- resolves recommended workflow mode from local routing rules
- explains routing source/reason
- writes intake artifact: `artifacts/intake/<task_id>/intake.json`
- writes Codex escalation packet when escalation is selected:
  - `artifacts/intake/<task_id>/codex-escalation-packet.json`
  - `artifacts/intake/<task_id>/codex-escalation-packet.md`

## Inputs
- `--name` (required)
- `--goal` (required)
- optional task class (`--class` or `--trigger` + `--fix-pattern`)
- optional escalation policy: `--escalate auto|yes|no` (default: `auto`)

## Escalation selection
- `auto`: escalate when recommended mode is not `tactical`
- `yes`: always produce escalation packet
- `no`: never produce escalation packet

## Usage
Direct:
```sh
./bin/local_task_intake.py --name "task-name" --goal "short objective"
```

With known class:
```sh
./bin/local_task_intake.py \
  --name "task-name" \
  --goal "short objective" \
  --class "hard-failure-analysis | state-coupled shell flow"
```

Via make:
```sh
TASK_NAME='task-name' TASK_GOAL='short objective' make local-task-intake
```

## Operator flow
1. Run intake.
2. If `escalation_selected=false`, Codex continues locally:
   - follow the recommended workflow mode while keeping Codex as the orchestrator (`WORKFLOW_MODE=<recommended> ./bin/aider_loop.sh --name ... --goal ...` when tactical automation is desired).
3. If `escalation_selected=true`, use packet artifact for Codex handoff and then continue normal loop.
4. Capture -> evaluate -> plan -> refresh rules as usual.
