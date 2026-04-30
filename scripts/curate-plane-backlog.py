#!/usr/bin/env python3
"""Plane backlog curation: label assignment via title-prefix mapping.

Usage:
    python3 scripts/curate-plane-backlog.py [--dry-run]

Env: PLANE_API_TOKEN, PLANE_PROJECT_ID, PLANE_WORKSPACE (or defaults from connector).
"""
import sys
import os
import time
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from framework.plane_connector import PlaneAPI, RateLimitError

DRY_RUN = "--dry-run" in sys.argv

# Prefix → label UUID (built from Phase 14 curation audit 2026-04-30)
LABEL_MAP: dict[str, str] = {
    "[RM-TESTING-":  "ee0f4b66-4e36-4ad1-9ac7-a0baf3785e47",
    "[RM-DOCS-":     "14374a9c-09b7-47ca-bfd4-481e5a0eebf7",
    "[RM-DATA-":     "df1ab489-5558-473d-9327-ffeabacd9791",
    "[RM-CLI-":      "351c499f-4e00-4424-a959-998167cf2989",
    "[RM-MONITOR-":  "8b5c320e-d140-44a3-b962-bbc6f5e1ed54",
    "[RM-MON-":      "8b5c320e-d140-44a3-b962-bbc6f5e1ed54",
    "[RM-UTIL-":     "f9092756-c875-4d38-96c3-515a92b92dac",
    "[RM-SECURITY-": "f767467a-abc5-4669-b9d5-4d3111db0711",
    "[RM-REFACTOR-": "5d7d05a9-94bd-4229-bb23-6e50fb2dfb8f",
    "[RM-CONFIG-":   "27be076e-91e7-4c88-97fc-05d2f2fcc87a",
    "[RM-API-":      "a02e934b-53d3-4162-a2ef-3c4f9c144cb2",
    "[RM-MEDIA-":    "71083338-33f4-4dac-9422-8983af626f60",
    "[RM-OPS-":      "cce5a257-5351-4f03-8ccd-691c35ac06f6",
    "[RM-DEV-":      "96810e90-d119-4eda-be07-0bdae86050f1",
    "[RM-UX-":       "4fac9819-a56c-42f6-b133-26c569db7ffb",
    "[RM-USERMGMT-": "d817e298-cad1-46c6-b12b-a29d585b80ad",
    "[RM-SCALE-":    "69522a9e-8419-4eae-b7a8-7b72b1e1031d",
    "[RM-PERF-":     "d21390a4-85eb-4299-86a3-d70d546a3afa",
    "[RM-INT-":      "d7e27871-bd43-493d-b9bb-1da68b500fc5",
    "[RM-FLOW-":     "a6f42110-2f99-48d4-9c21-00fee2223ae7",
    "[RM-DEPLOY-":   "dcacf841-29de-4b64-8710-ab634612393f",
    "[RM-CI-":       "ef2c9a58-e0f0-4f4b-be92-6d844a18324f",
    "[RM-BACKUP-":   "f4b5e08e-89ab-43ff-92e3-f2c275de44cd",
    "[RM-APIGW-":    "9f9d17a1-cbce-4f40-b20c-139b0f9ee0c8",
    "[RM-UI-":       "2523d6fb-4082-4f86-ab10-839b11b2daf3",
    "[RM-GOV-":      "11efb3f4-75a0-4cad-8be3-d3583146e95a",
    "[RM-SHOP-":     "d2382495-a64d-4973-ab05-01224ac1ffff",
    "[RM-HOME-":     "c0b7f02a-bb4b-469d-ac89-1461e8ce2984",
    "[RM-AUTO-MECH-":"a2023a0c-c6a6-4cc7-80c3-833d45dba913",
    "[RM-AUTO-":     "97d82532-898f-4f3a-813e-64d527fdc2f9",
    "[RM-SEC-":      "876d7acd-2f54-41b6-9c86-9815c413010d",
    "[RM-REL-":      "244c11b9-33da-49e7-bc3e-b23b6f63025e",
    "[RM-QA-":       "f2a226e2-9758-4f87-b8f1-bb888706e3be",
    "[RM-PLUGIN-":   "3f33e7bc-9675-4d08-b51b-ad687edef3f7",
    "[RM-OBS-":      "67b335f7-bb3d-4b45-b00c-82072465b48c",
    "[RM-MOBILE-":   "74e7308a-c236-4d18-ad22-d44c8fda6fc3",
    "[RM-I18N-":     "a5386950-bbcb-4963-a947-a36a5e87fe61",
    "[RM-A11Y-":     "4c40bf11-8313-434b-9a5a-122a63e67263",
    "[RM-LEARN-":    "be03fd1a-c448-4e82-b8e3-f76da15f3d8f",
    "[RM-INV-":      "7491cc9d-d664-4485-b2ae-aaa631c0068e",
    "[RM-LANG-":     "03f94393-eceb-4630-a907-9594fde544a1",
    "[RM-KB-":       "7e9a7f6e-41ce-4fa6-a92c-991d76ec20d7",
    "[RM-INTEL-":    "5c390cc6-8858-4381-8ea9-dcd3c024b50f",
    "[RM-HW-":       "37c00a0e-8d67-4b8f-97ef-0f4e2889453b",
    "[RM-PERIPH-":   "f1b82e82-7242-46f0-a8e6-8589e0b9ea9d",
}

api = PlaneAPI()

issues = api.list_all_issues()
print(f"Total issues: {len(issues)}", flush=True)

def get_label_id(title: str) -> Optional[str]:
    for prefix, uid in LABEL_MAP.items():
        if title.startswith(prefix):
            return uid
    return None

first_write_verified = False
writes = 0
skipped = 0
errors = 0

for i, issue in enumerate(issues):
    title = issue.get("name", "")
    label_id = get_label_id(title)
    if label_id is None:
        skipped += 1
        continue

    current_labels = issue.get("labels", [])
    if label_id in current_labels:
        skipped += 1
        continue

    new_labels = current_labels + [label_id]

    if DRY_RUN:
        print(f"  DRY: #{issue.get('sequence_id','?')} {title[:60]}")
        writes += 1
        continue

    issue_url = api._proj_url(f"/issues/{issue['id']}/")
    try:
        api._patch(issue_url, {"labels": new_labels})
        writes += 1

        # §4 first-batch-verify: read back after first write
        if not first_write_verified:
            readback = api._get(issue_url)
            actual = readback.get("labels", [])
            if label_id not in actual:
                print(f"ABORT: first-batch-verify failed — label not in readback {actual}",
                      file=sys.stderr)
                sys.exit(2)
            first_write_verified = True
            print(f"  VERIFIED: first write landed on #{issue.get('sequence_id','?')} ({issue['id'][:8]})",
                  flush=True)

        if writes % 50 == 0:
            print(f"  Progress: {writes} writes, {i+1}/{len(issues)} scanned", flush=True)

        time.sleep(1.5)  # §3 pace: 60 req/min

    except RateLimitError as exc:
        print(f"  RATE-LIMIT at #{issue.get('sequence_id','?')}: {exc} — sleeping 65s",
              file=sys.stderr)
        time.sleep(65)
        try:
            api._patch(issue_url, {"labels": new_labels})
            writes += 1
            time.sleep(1.5)
        except Exception as retry_exc:
            print(f"  RETRY-FAIL: {retry_exc}", file=sys.stderr)
            errors += 1

    except Exception as exc:
        print(f"  ERROR #{issue.get('sequence_id','?')}: {exc}", file=sys.stderr)
        errors += 1

print(f"\nDone. writes={writes} skipped={skipped} errors={errors}", flush=True)
