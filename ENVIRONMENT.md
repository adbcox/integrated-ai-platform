# Codex Environment

## Active identity
- Primary host project path:
  - /srv/platform/repos/platform-browser-operator
- Active compose service/container identity:
  - platform-browser-operator

## Compatibility status
- Legacy repo symlink:
  - /srv/platform/repos/qnap-browser-operator
  - retired in Wave D; kept only as a renamed rollback artifact if present.
- Compatibility wrappers:
  - qnap_*.sh wrappers were retired in Wave B and archived under .compat-archive.

## Container
- Container project path:
  - /app
- Expected user:
  - root

## Codex
- Required Node version:
  - 22
- Start command:
  - /app/start_codex.sh

## Recommended workflow
1. SSH to the primary host
2. Open the project directory
3. Run:
   - ./start_codex.sh

## Quick checks
Inside the container or host shell, verify:
- pwd
- whoami
- node -v
- which codex

Expected values:
- node -v => v22.x
