"""Reference config for the Tricolor example (non-runnable archive)."""

from pathlib import Path

# example_past_converter root (this file's parent)
PROJECT_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PROJECT_ROOT.parent

dataset_id = "tricolor_projections"
animal_id = "exp101-a1"
session_id = "20260204-gratings"

raw_session_root = PROJECT_ROOT / "EXAMPLE_SESSION_DIR_GOES_HERE" / "example_session"
output_dataset_root = PROJECT_ROOT / "EXAMPLE_SURFORMAT_DATASET_WILL_APPEAR_HERE"
access_code_root = PROJECT_ROOT / "EXAMPLE_ACCESS_CODE_GOES_HERE"

sur_nwb_conversion_table_path = REPO_ROOT / "agent_materials" / "sur_nwb_conversion_table.csv"
custom_to_sur_mapping_table_path = PROJECT_ROOT / "custom_to_sur_mapping_table.csv"

verbose = False
voltage_ttl_threshold_v = 4.9

log_path = PROJECT_ROOT / "logs" / "run.log"
