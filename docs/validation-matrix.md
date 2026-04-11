# Validation Matrix

Use this matrix to run only the checks needed for the files you changed.

| Changed area | Fast check | Behavior check |
| --- | --- | --- |
| `browser_operator_open_app.sh`, `browser_operator_login_flow.sh` | `make quick` | `./tests/run_offline_scenarios.sh open-app-deep-loaded open-app-modal-blocked open-app-missing-session` |
| `browser_operator_open_and_click.sh` | `make quick` | `./tests/run_offline_scenarios.sh open-and-click-hit open-and-click-miss` |
| `browser_operator_open_container_target.sh` | `make quick` | `./tests/run_offline_scenarios.sh open-container-target-deep-loaded open-container-target-modal-blocked` |
| `shell/common.sh`, `tests/mock_bop.sh`, `tests/mock_login_flow.sh`, `tests/scenarios/*`, `tests/run_offline_scenarios.sh` | `make quick` | `make test-offline` |
| Top-level `*.py` | `make quick` | `make check` (when broader confidence is needed) |
| Docs only (`README.md`, `AGENTS.md`, `docs/*`) | none required | none required |

## Shortcuts
- Fast local loop: `make quick`
- Changed-scope offline behavior tests: `make test-changed-offline`
- Full deterministic offline suite: `make test-offline`
- Full quick static check (shell + python): `make check`
