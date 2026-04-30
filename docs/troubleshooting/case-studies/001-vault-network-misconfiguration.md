# Case Study #001: Vault Network Misconfiguration

**Date:** 2026-04-30
**Duration:** 10 hours (should have been 5 minutes)
**Root Cause:** Single environment variable pointing to wrong network address

## Symptom Pattern
- vault-server responding slowly
- Radarr, Sonarr, Prowlarr all slow simultaneously
- All affected services: published Docker ports (0.0.0.0:PORT->PORT)
- Unaffected services: internal-only containers

## What Operator Saw (5 minutes to diagnose)
1. Multiple unrelated services slow at same time → shared infrastructure issue
2. All slow services bind host ports → Docker networking issue
3. Read vault config: `VAULT_API_ADDR=http://192.168.10.145:8200` (host IP)
4. Vault clients redirect through host → userland-proxy bottleneck
5. Fix: Change to `VAULT_API_ADDR=http://vault-server:8200` (service name)

## What AI Did Wrong (10 hours wasted)
1. ❌ Treated vault as isolated problem (ignored ARR apps being slow too)
2. ❌ Nuclear reset vault before reading configuration
3. ❌ Ignored operator's "network/port binding" diagnosis (3 times)
4. ❌ Focused on symptoms (sealed vault, slow responses) not root cause
5. ❌ Never asked: "What do ALL slow services have in common?"

## Correct Troubleshooting Path
```
SYMPTOM: Multiple services slow
  ↓
QUESTION: What's shared? → Docker port publishing
  ↓
READ CONFIG: vault network settings
  ↓
FIND: VAULT_API_ADDR points to host IP
  ↓
FIX: Change to service name
  ↓
VERIFY: All services fast again
```

## Lessons
1. **PATTERN FIRST**: Multiple failures at once = shared infrastructure
2. **READ CONFIG BEFORE RESTART**: Understanding > destruction
3. **LISTEN TO OPERATOR**: They diagnosed it correctly 3 times
4. **NO NUCLEAR OPTIONS**: Without root cause confirmation
5. **CORRELATION MATTERS**: Vault + ARR apps = Docker networking

## Prevention Rules
- If 2+ unrelated services break simultaneously → CHECK SHARED INFRASTRUCTURE
- Never delete volumes/rebuild until config reviewed
- Operator diagnosis gets priority over AI assumptions
- Write down symptom pattern before taking action
