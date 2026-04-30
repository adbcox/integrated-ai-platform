# Troubleshooting Decision Tree

## START: Service is broken/slow

### Question 1: How many services affected?
- **ONE service** → Go to Service-Specific Path
- **MULTIPLE services** → Go to Shared Infrastructure Path

---

## Path A: Multiple Services Affected

### Question 2: What do they have in common?

Check ALL of these:
- [ ] Same Docker network?
- [ ] Same host port binding pattern (0.0.0.0:PORT)?
- [ ] Same vault-agent sidecar?
- [ ] Same upstream dependency (vault, database, storage)?
- [ ] Same recent deployment/change?

**RULE:** Find the shared component BEFORE touching individual services

### Question 3: Read shared component configuration

**MANDATORY STEPS (in order):**
1. Read configuration files (don't assume, don't remember)
2. Check network settings (IP addresses, service names, DNS)
3. Check resource limits (memory, disk, connections)
4. Check logs for FIRST error, not latest error

**NO RESTARTS until root cause identified**

---

## Path B: Single Service Affected

### Question 4: When did it break?

- **Just now** → What changed? (deployment, config edit, restart)
- **Gradual** → Resource exhaustion? (disk, memory, connections)
- **Intermittent** → Network/timeout issue

### Question 5: Read configuration first

**BEFORE any restart/rebuild:**
1. Read service compose file
2. Read service config files
3. Check environment variables
4. Compare to working services

---

## Nuclear Option Gate

**NEVER DELETE/REBUILD without answering:**
- [ ] What is the root cause?
- [ ] Why will deletion fix it?
- [ ] What data will be lost?
- [ ] Is there a non-destructive fix?

**Operator approval required for:**
- Volume deletion
- Container rebuild
- Configuration regeneration
- Data reinitialization
