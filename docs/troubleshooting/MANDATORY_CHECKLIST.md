# Mandatory Troubleshooting Checklist

**USE THIS BEFORE ANY DESTRUCTIVE ACTION**

## Phase 1: Information Gathering (READ ONLY)

- [ ] Document symptom pattern (what's broken, when, how many services)
- [ ] Read all relevant configuration files (don't assume)
- [ ] Check correlation: what else broke at same time?
- [ ] Timeline: what changed before it broke?
- [ ] Operator input: what do they think it is?

## Phase 2: Hypothesis

- [ ] State root cause hypothesis in one sentence
- [ ] Explain how symptoms match hypothesis
- [ ] Explain what's shared if multiple services affected
- [ ] Operator review: does this make sense?

## Phase 3: Verification

- [ ] Test hypothesis with read-only diagnostic
- [ ] If hypothesis wrong, return to Phase 1
- [ ] If hypothesis correct, proceed to Phase 4

## Phase 4: Fix

- [ ] Propose minimal fix (smallest change possible)
- [ ] Explain why fix addresses root cause
- [ ] Document what will happen during fix
- [ ] Get operator approval
- [ ] Execute fix
- [ ] Verify symptoms resolved

## RED FLAGS (STOP IMMEDIATELY)

🚨 **Multiple services affected** → Shared infrastructure issue
🚨 **Operator says it's X** → Listen, don't dismiss
🚨 **About to delete data** → Do you know root cause?
🚨 **About to restart** → Have you read config?
🚨 **Assumption-based fix** → Verify first
