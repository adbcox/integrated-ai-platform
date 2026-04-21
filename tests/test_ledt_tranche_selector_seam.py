import os
import json
from datetime import datetime, timedelta
from unittest.mock import patch, mock_open
from bin.run_ledt_tranche_selector import score_blocks, read_lace2_closeout, write_tranche_selection, main

def test_score_blocks():
    # Mock _collect_shared_touch_surfaces to return a fixed number of touch surfaces
    with patch('bin.run_ledt_tranche_selector._collect_shared_touch_surfaces', return_value=['touch1', 'touch2']):
        blocks = [
            {"block_id": "LEDT-BLOCK-1", "base_score": 0.8},
            {"block_id": "LEDT-BLOCK-2", "base_score": 0.75}
        ]
        scored_blocks = score_blocks(blocks)
        assert scored_blocks[0]['final_score'] == 0.9
        assert scored_blocks[1]['final_score'] == 0.8

def test_read_lace2_closeout():
    # Mock the file content
    mock_content = json.dumps({
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
    })

    with patch('builtins.open', mock_open(read_data=mock_content)):
        closeout = read_lace2_closeout()
        assert closeout['campaign_verdict'] == "lace2_campaign_complete"

def test_write_tranche_selection(tmp_path):
    # Create a temporary file path
    output_path = tmp_path / 'tranche_selection.json'

    tranche_selection = {
        "campaign_id": "LEDT",
        "tranche_id": "LEDT-TRANCHE-1",
        "lace2_upstream_verdict": "lace2_campaign_complete",
        "selected_blocks": [],
        "scoring_method": "rm_gov_003_shared_touch_count",
        "selected_at": datetime.utcnow().isoformat()
    }

    write_tranche_selection(tranche_selection, output_path=str(output_path))

    # Check if the file was written correctly
    assert os.path.exists(output_path)
    with open(output_path, 'r') as f:
        content = json.load(f)
        assert content == tranche_selection

def test_run_ledt_tranche_selector(tmp_path):
    # Mock the LACE2 closeout file content
    mock_content = json.dumps({
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
    })

    # Mock the file reading
    with patch('builtins.open', mock_open(read_data=mock_content)):
        # Monkeypatch the output path to use tmp_path
        with patch('bin.run_ledt_tranche_selector.write_tranche_selection') as mock_write:
            main()

            # Check if write_tranche_selection was called with correct arguments
            mock_write.assert_called_once()
            args, kwargs = mock_write.call_args
            tranche_selection = args[0]
            output_path = args[1]

            assert tranche_selection['campaign_id'] == "LEDT"
            assert tranche_selection['tranche_id'] == "LEDT-TRANCHE-1"
            assert tranche_selection['lace2_upstream_verdict'] == "lace2_campaign_complete"
            assert len(tranche_selection['selected_blocks']) == 5
            assert tranche_selection['scoring_method'] == "rm_gov_003_shared_touch_count"

            # Validate the selected_at timestamp is within a reasonable range
            selected_at = datetime.fromisoformat(tranche_selection['selected_at'])
            now = datetime.utcnow()
            assert now - timedelta(seconds=10) <= selected_at <= now + timedelta(seconds=10)

            # Check if the output path is in tmp_path
            assert str(output_path).startswith(str(tmp_path))
