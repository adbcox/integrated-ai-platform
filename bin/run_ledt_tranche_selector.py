import json
from datetime import datetime
import os
import sys

# Add the parent directory to sys.path to make roadmap_governance importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from roadmap_governance.planner_service import _collect_shared_touch_surfaces

# Define the five transition feature blocks inline with base_score and touch_surfaces
transition_feature_blocks = [
    {"block_id": "LEDT-BLOCK-1", "base_score": 0.8},
    {"block_id": "LEDT-BLOCK-2", "base_score": 0.75},
    {"block_id": "LEDT-BLOCK-3", "base_score": 0.7},
    {"block_id": "LEDT-BLOCK-4", "base_score": 0.65},
    {"block_id": "LEDT-BLOCK-5", "base_score": 0.6}
]

def score_blocks(blocks):
    for block in blocks:
        shared_touch_surfaces = _collect_shared_touch_surfaces([block["block_id"]])
        block["final_score"] = block["base_score"] + 0.05 * len(shared_touch_surfaces)
    return sorted(blocks, key=lambda x: x["final_score"], reverse=True)

def read_lace2_closeout(file_path='artifacts/expansion/LACE2/LACE2_closeout.json'):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("LACE2 closeout file not found.")
        return None
    except json.JSONDecodeError:
        print("Invalid JSON in LACE2 closeout file.")
        return None

def write_tranche_selection(tranche_selection, output_path='artifacts/expansion/LEDT/tranche_selection.json'):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(tranche_selection, f, indent=4)

def main():
    # Read artifacts/expansion/LACE2/LACE2_closeout.json
    lace2_closeout = read_lace2_closeout()
    if not lace2_closeout:
        return

    # Hard-stop if campaign_verdict is missing
    if 'campaign_verdict' not in lace2_closeout or lace2_closeout['campaign_verdict'] != 'lace2_campaign_complete':
        print("Campaign verdict missing or incorrect.")
        return

    # Score the blocks
    scored_blocks = score_blocks(transition_feature_blocks)

    # Emit the results to artifacts/expansion/LEDT/tranche_selection.json
    tranche_selection = {
        "campaign_id": "LEDT",
        "tranche_id": "LEDT-TRANCHE-1",
        "lace2_upstream_verdict": lace2_closeout['campaign_verdict'],
        "selected_blocks": scored_blocks,
        "scoring_method": "rm_gov_003_shared_touch_count",
        "selected_at": datetime.utcnow().isoformat()
    }

    write_tranche_selection(tranche_selection)

if __name__ == "__main__":
    main()
