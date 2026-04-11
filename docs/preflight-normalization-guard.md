# Preflight Normalization Guard

This guard verifies both normalized repositories are in a trusted baseline state before running Aider/Codex task loops.

## Default checks
- required tools exist (`bash`, `git`, `sed`, `awk`, `python3`, `aider`, `ollama`)
- both repo paths exist and are valid git repos
- each repo is on an explicit branch matching `EXPECTED_BRANCH` (default: `main`)
- each repo contains `docs/repo-normalization-status.md` with `intentional-local-baseline`
- each repo working tree is clean (or acknowledged with `ALLOW_DIRTY=1`)

## Usage
- direct: `./bin/preflight_normalization_guard.sh`
- make: `make preflight-normalization-guard`

## Environment overrides
- `REPOS_ROOT`
- `BROWSER_OPERATOR_REPO`
- `CONTROL_PLANE_REPO`
- `EXPECTED_BRANCH`
- `ALLOW_DIRTY` (`0` by default)
- `REQUIRED_TOOLS` (space-separated override list)
