import os
import json
from datetime import datetime, timedelta
from unittest.mock import patch
from bin.run_ledt_tranche_selector import score_blocks, main

def test_score_blocks():
    # Mock _collect_shared_touch_surfaces to return a fixed number of touch surfaces
    with patch('roadmap_governance.planner_service._collect_shared_touch_surfaces', return_value=['touch1', 'touch2']):
        blocks = [
            {"block_id": "LEDT-BLOCK-1", "base_score": 0.8},
            {"block_id": "LEDT-BLOCK-2", "base_score": 0.75}
        ]
        scored_blocks = score_blocks(blocks)
        assert scored_blocks[0]['final_score'] == 0.9
        assert scored_blocks[1]['final_score'] == 0.8

def test_run_ledt_tranche_selector():
    # Ensure LACE2 closeout file exists and is valid
    with open('artifacts/expansion/LACE2/LACE2_closeout.json', 'w') as f:
        json.dump({
            "closeout_id": "LACE2-CLOSE-20260421120426",
            "campaign_id": "LACE2",
            "campaign_verdict": "lace2_campaign_complete",
            "packets_completed": 15,
            "packets_expected": 15,
            "artifacts_present": 12,
            "artifacts_expected": 12,
            "modules_importable": 13,
            "modules_expected": 13,
            "what_was_built": [],
            "what_was_proved": [],
            "what_remains_unproven": [],
            "known_limitations": [],
            "lace2_autonomy_verdict": "real_local_autonomy_uplift_confirmed",
            "selected_mini_tranche": "MT2-TRACE-REPLAY-PIPELINE",
            "closed_at": "2026-04-21T12:04:26+00:00"
        }, f)

    # Run the tranche selector
    main()

    # Check if tranche_selection.json exists and is valid
    assert os.path.exists('artifacts/expansion/LEDT/tranche_selection.json')
    with open('artifacts/expansion/LEDT/tranche_selection.json', 'r') as f:
        tranche_selection = json.load(f)

    # Validate the contents of tranche_selection.json
    assert tranche_selection['campaign_id'] == "LEDT"
    assert tranche_selection['tranche_id'] == "LEDT-TRANCHE-1"
    assert tranche_selection['lace2_upstream_verdict'] == "lace2_campaign_complete"
    assert len(tranche_selection['selected_blocks']) == 5
    assert tranche_selection['scoring_method'] == "rm_gov_003_shared_touch_count"

    # Validate the selected_at timestamp is within a reasonable range
    selected_at = datetime.fromisoformat(tranche_selection['selected_at'])
    now = datetime.utcnow()
    assert now - timedelta(seconds=10) <= selected_at <= now + timedelta(seconds=10)
