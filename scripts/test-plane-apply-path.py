#!/usr/bin/env python3
"""Discovery #13 — integration test for connector apply path.

Run against a staging/sandbox project; tears down created issue.
Never run against the production roadmap project.

Usage:
    PLANE_STAGING_PROJECT_ID=<id> python3 scripts/test-plane-apply-path.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from framework.plane_connector import PlaneAPI, RateLimitError  # noqa: E402

STAGING_PROJECT_ID = os.environ.get("PLANE_STAGING_PROJECT_ID")
if not STAGING_PROJECT_ID:
    print("PLANE_STAGING_PROJECT_ID not set — cannot run apply-path test")
    sys.exit(1)

api = PlaneAPI()
api._project_id = STAGING_PROJECT_ID   # override to staging

print("Step 1: create test issue")
try:
    issue = api.create_issue(
        name="[apply-path-test] D#13 integration test — delete me",
        description="Automated apply-path smoke test. Will be deleted.",
        priority="low",
        external_id="apply-path-test-D13",
    )
except RateLimitError:
    time.sleep(60)
    issue = api.create_issue(
        name="[apply-path-test] D#13 integration test — delete me",
        description="Automated apply-path smoke test. Will be deleted.",
        priority="low",
        external_id="apply-path-test-D13",
    )
issue_id = issue["id"]
print(f"  Created: {issue_id}")

print("Step 2: verify creation (first-batch-verify pattern)")
if not api.verify_issue_field(issue_id, "name", "[apply-path-test] D#13 integration test — delete me"):
    print("FAIL: name field not persisted after POST")
    sys.exit(1)
print("  name verified")

print("Step 3: apply a label update")
try:
    labels = api.list_labels()
except RateLimitError:
    time.sleep(60)
    labels = api.list_labels()

label_results = labels if isinstance(labels, list) else labels.get("results", [])
if label_results:
    label_id = label_results[0]["id"]
    api.update_issue(issue_id, {"labels": [label_id]})
    time.sleep(1.5)
    if not api.verify_issue_field(issue_id, "labels", [label_id]):
        print("FAIL: label update not persisted")
        sys.exit(1)
    print("  label update verified")
else:
    print("  SKIP: no labels in staging project to test with")

print("Step 4: apply a state transition")
states = api.list_states()
done_state = next((s["id"] for s in states if s["name"].lower() in ("done", "closed")), None)
if done_state:
    api.update_issue_state(issue_id, "Done")
    time.sleep(1.5)
    reopened = api._get(api._proj_url(f"/issues/{issue_id}/"))
    print(f"  state after: {reopened.get('state_detail', {}).get('name', '?')}")

print("Step 5: delete test issue")
try:
    deleted = api._delete(api._proj_url(f"/issues/{issue_id}/"))
    print(f"  deleted: {deleted}")
except Exception as exc:
    print(f"  delete failed (manual cleanup needed for {issue_id}): {exc}")

print("PASS: apply-path integration test complete")
