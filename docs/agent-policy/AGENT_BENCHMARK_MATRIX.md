# Agent Benchmark Matrix

**WBS 8.3** — Defines the task classes and benchmark structure for agent promotion evaluation.

## Overview

The benchmark matrix establishes 8 standardized task classes that evaluate agent capabilities across different code engineering scenarios. Each task class has defined success criteria, difficulty level, and expected performance characteristics.

## Task Classes

### 1. Code Generation from Specification

**Description:** Write new code from a natural language specification or design document.

**Task Example:** "Create a Python CLI tool that reads CSV files and outputs JSON"

**Success Criteria:**
- Code executes without syntax errors
- Implements 90%+ of specified requirements
- Handles common error cases
- Includes appropriate error messages

**Difficulty:** Medium
**Expected Duration:** 5-15 minutes
**Complexity Indicators:** Specification clarity, requirement count, API familiarity

**Measured Metrics:**
- Time to first working version
- Token count
- Number of iterations to correctness
- Code quality (linting, type hints)

---

### 2. Bug Fixing

**Description:** Identify and resolve defects in existing code.

**Task Example:** "Fix the memory leak in the event loop cleanup function"

**Success Criteria:**
- Bug is reproduced by test case
- Root cause is identified in code
- Fix is minimal and surgical
- No regressions in existing tests
- Fix addresses the root cause, not symptoms

**Difficulty:** Medium-High
**Expected Duration:** 10-30 minutes
**Complexity Indicators:** Bug locality, test availability, debugging information

**Measured Metrics:**
- Time to root cause identification
- Number of failed fix attempts
- Surgical score (lines changed vs. scope)
- Test pass rate post-fix

---

### 3. Refactoring

**Description:** Improve code structure, readability, or performance without changing behavior.

**Task Example:** "Extract common validation logic into a shared utility function"

**Success Criteria:**
- Behavior is unchanged (all tests pass)
- Code is more maintainable or performant
- Naming is clear and consistent
- No dead code introduced
- Changes are cohesive and focused

**Difficulty:** Medium
**Expected Duration:** 10-25 minutes
**Complexity Indicators:** Scope of changes, file count, test coverage

**Measured Metrics:**
- Lines changed vs. files modified
- Test pass rate
- Cyclomatic complexity reduction
- Code coverage preservation

---

### 4. Test Writing

**Description:** Create or extend test suites for existing code.

**Task Example:** "Write unit tests for the authentication module with 90% coverage"

**Success Criteria:**
- Tests are executable and pass
- Coverage target is met (typically 80%+)
- Tests verify behavior, not implementation
- Edge cases and error paths are tested
- Tests are maintainable and readable

**Difficulty:** Medium
**Expected Duration:** 15-30 minutes
**Complexity Indicators:** Code complexity, test framework familiarity, coverage target

**Measured Metrics:**
- Coverage percentage
- Test execution time
- Number of test cases
- False positive rate

---

### 5. Documentation Writing

**Description:** Create or update documentation for code, APIs, or systems.

**Task Example:** "Write API documentation for the new payment service endpoints"

**Success Criteria:**
- Documentation is accurate and complete
- Examples are working and relevant
- Formatting is consistent
- No outdated or misleading information
- Accessibility guidelines are met

**Difficulty:** Low-Medium
**Expected Duration:** 10-20 minutes
**Complexity Indicators:** Documentation scope, code complexity, audience level

**Measured Metrics:**
- Documentation completeness score
- Clarity assessment
- Example accuracy
- Cross-reference validity

---

### 6. Performance Optimization

**Description:** Improve code performance or resource utilization.

**Task Example:** "Reduce the latency of the search endpoint from 500ms to 100ms"

**Success Criteria:**
- Performance target is met
- No correctness regressions
- Trade-offs are documented
- Improvement is measurable and sustained
- Resource usage is reasonable

**Difficulty:** High
**Expected Duration:** 20-45 minutes
**Complexity Indicators:** Performance target, code complexity, profiling data available

**Measured Metrics:**
- Latency reduction percentage
- Memory footprint change
- CPU utilization change
- Profiling data alignment

---

### 7. Security Vulnerability Remediation

**Description:** Identify and fix security vulnerabilities in code.

**Task Example:** "Fix SQL injection vulnerability in the user search endpoint"

**Success Criteria:**
- Vulnerability is eliminated
- Attack vector is documented
- Fix does not introduce new vulnerabilities
- Performance impact is acceptable
- Affected systems are tested

**Difficulty:** High
**Expected Duration:** 15-40 minutes
**Complexity Indicators:** Vulnerability severity, attack surface, remediation complexity

**Measured Metrics:**
- Vulnerability elimination confirmation
- CVSS score reduction
- Fix validation against attack patterns
- Code audit sign-off

---

### 8. Multi-File Coordination

**Description:** Execute changes spanning multiple files or modules with consistent semantics.

**Task Example:** "Rename a core interface and update all 12 callers throughout the codebase"

**Success Criteria:**
- All files are updated consistently
- No broken references or type mismatches
- Tests pass across all affected modules
- Refactoring is complete and coherent
- No partial or inconsistent updates

**Difficulty:** High
**Expected Duration:** 20-35 minutes
**Complexity Indicators:** File count, dependency complexity, search/replace complexity

**Measured Metrics:**
- File count accuracy
- Consistency check (all references updated)
- Test pass rate
- Build/compile success
- Correctness verification

---

## Benchmark Scoring

For each task class, agents are scored on:

1. **Correctness** (0-100): Does the deliverable meet requirements?
2. **Completeness** (0-100): Are all specified items addressed?
3. **Quality** (0-100): Code style, error handling, documentation
4. **Efficiency** (0-100): Time and token consumption vs. baseline
5. **Safety** (0-100): Constraint compliance, no destructive errors

**Promotion Threshold:** 75+ average across all metrics and task classes.

## Baseline Comparison

All agent performance is compared against:
- **Aider (primary baseline):** Extended Aider AI with git integration
- **Cline (secondary baseline):** MCP-based agent
- **Human Engineer (ceiling):** Human developer solving same tasks

## Recurrence Testing

For promotion to production, agents must demonstrate 90%+ consistency across 3 independent runs of the same task, with:
- ±5% variance in token consumption
- ±10% variance in duration
- 100% correctness rate (all runs produce correct output)

---

**Last Updated:** 2026-05-10
**Related:** AGENT_VERIFIER_GATES.md, AGENT_LANE_POLICY.md
