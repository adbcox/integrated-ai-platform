# KI-001: plane-api worker OOM/SIGKILL events

## Status
RESOLVED — Real cause was gunicorn `WORKER TIMEOUT` (default 30s), not memory pressure. Set `GUNICORN_TIMEOUT=120` and added `mem_limit: 2G` to plane-api in docker-compose-plane.yml. Container observed for 150s with 0 restart events and 0 SIGKILL/SIGABRT log entries.

## Observation
docker-plane-api-1 logs show recurring:
```
Worker (pid:NNN) was sent SIGKILL! Perhaps out of memory?
```

## Impact
Container reports healthy. /api endpoints respond 200. Workers are being
restarted by gunicorn after kills. User-facing impact appears minimal but
not zero — long-running requests may be cut short.

## Diagnosis needed
- Memory limit on docker-plane-api-1 vs actual usage
- Whether OOM is container-level (cgroup) or host-level
- Worker count vs available memory

## Created
Mon Apr 27 19:50:01 EDT 2026
