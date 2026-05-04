# Hand-grade packet 07 — T3-A agentic ag-incident-response

**Run:** 20260503T170223Z
**Model:** gemma2:27b on mac-studio
**Workload:** agentic
**Task ID:** ag-incident-response

## Auto-grader output

- score: **0.8333333333333334**
- pass: **True**
- notes: 5/6 steps present, 5 in order
- wall_s: 20.10594091699977, tps: 34.78512816637251

## Task summary

Plan incident response for production outage

## Model response (full)

```
## Incident Response Plan: Production API Returning 500 Errors

**Incident:** Production API returning 500 Internal Server Errors on 80% of requests.

**Timeline:** Issue started 2 minutes ago. Last deploy was 30 minutes ago.

**Goal:** Restore service availability and identify the root cause of the issue.

**Plan:**

**Phase 1: Triage (Verify Service Impact & Gather Initial Data)**

1. **Verify Error Rate:**
    *  Use monitoring tools to confirm the 80% error rate for API requests.
    * **Verification:** Screenshot or log showing the error rate from monitoring dashboards.
2. **Identify Affected Endpoints:**
    * Determine which specific API endpoints are experiencing errors.
    * **Verification:** List of affected endpoints and their corresponding error rates.
3. **Check Recent Changes:**
    * Review the last deployment (30 minutes ago) for any code changes, configuration updates, or infrastructure modifications that could be related to the issue.
    * **Verification:** Deployment logs, commit history, and change management records.

**Phase 2: Mitigation (Minimize Impact & Restore Service)**

1. **Roll Back Last Deployment (If Suspected):**
    * If the deployment is suspected as the cause, initiate a rollback to the previous stable version.
    * **Verification:** Successful rollback confirmation from deployment tools and monitoring dashboards showing error rate reduction.
2. **Implement Temporary Workarounds (If Necessary):**
    * Depending on the nature of the issue, consider implementing temporary workarounds like rate limiting, circuit breakers, or fallback mechanisms to mitigate the impact on users.
    * **Verification:** Documentation of implemented workarounds and their effectiveness in reducing error rates.

**Phase 3: Root Cause Analysis (Identify Underlying Issue)**

1. **Analyze Logs:**
    * Examine application logs, server logs, and database logs for any error messages, exceptions, or unusual patterns that could provide clues about the root cause.
    * **Verification:** Log excerpts highlighting relevant information and potential error sources.
2. **Debug Code (If Applicable):**
    * If code changes are suspected, use debugging tools to step through the affected code paths and identify any logic errors or unexpected behavior.
    * **Verification:** Documentation of debugging findings and potential code fixes.
3. **Review Infrastructure Configuration:**
    * Check server configurations, network settings, database connections, and other infrastructure components for any misconfigurations or resource limitations that could be contributing to the issue.
    * **Verification:** Documentation of infrastructure review findings and any identified issues.

**Post-Incident Actions:**

1. **Document Findings:** Create a detailed incident report summarizing the timeline, impact, mitigation steps taken, root cause analysis, and lessons learned.
2. **Implement Corrective Actions:** Address the identified root cause by fixing bugs, updating configurations, or implementing preventative measures to avoid similar issues in the future.
3. **Communicate with Stakeholders:** Inform affected users about the incident, its resolution, and any steps taken to prevent recurrence.

**Note:** This plan is a general framework and may need to be adapted based on the specific details of the incident and your organization's processes.
```

## Operator scoring

- [ ] coherent? (yes / no)
- [ ] addresses task? (yes / partial / no)
- [ ] ship-ready quality? (yes / no)
- [ ] auto-grade fair? (yes / too-low / too-high) — by how much?
- [ ] hand-grade 0.00-1.00: ___
- [ ] notes:
