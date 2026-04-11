# Local Routing Rules

This layer applies local-model improvement planning outputs to practical workflow-mode routing.

## Rule file
Generated policy:
- `policies/local-routing-rules.json`

This file contains:
- `default_workflow_mode`
- class-specific overrides keyed by `<trigger> | <fix_pattern>`
- trigger-level fallback defaults
- decision framework metadata from planning output

## Mode mapping model
Task classes route to one of:
1. `local-first` -> `tactical`
2. `local-with-codex-assist` -> `codex-assist`
3. `codex-preferred` -> `codex-investigate`
4. `codex-required-for-now` -> `codex-failure`

## Generate / refresh rules
```sh
make local-model-rules-refresh
```

This runs evaluation + planning refresh, then regenerates routing rules.

## Inspect rules
```sh
make local-model-rules-show
```

## Resolve a mode for a task class
By class key:
```sh
TASK_CLASS='hard-failure-analysis | state-coupled shell flow' make local-model-route
```

By trigger + pattern:
```sh
TRIGGER='hard-failure-analysis' FIX_PATTERN='state-coupled shell flow' make local-model-route
```

Direct selector usage:
```sh
./bin/select_workflow_mode.py --class 'hard-failure-analysis | state-coupled shell flow'
./bin/select_workflow_mode.py --class 'hard-failure-analysis | state-coupled shell flow' --shell-export
```

## Practical operator flow
1. Run `make local-model-rules-refresh` after a batch of escalations.
2. Start new work from intake:
   - `TASK_NAME='<task>' TASK_GOAL='<goal>' [TASK_CLASS='<trigger> | <fix_pattern>'] make local-task-intake`
3. Resolve/confirm recommended mode for current task class.
4. Set `WORKFLOW_MODE` accordingly and run `aider_loop`.
5. Repeat cycle; apply only small rule changes per iteration.
