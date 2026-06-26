"""Project configuration — fill when implementing a new converter."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

################
# main config
#################

dataset_id = ""
animal_id = ""
session_id = ""

raw_session_root = PROJECT_ROOT / "EXAMPLE_SESSION_DIR_GOES_HERE" / "example_session"
output_dataset_root = PROJECT_ROOT / "EXAMPLE_SURFORMAT_DATASET_WILL_APPEAR_HERE"
access_code_root = PROJECT_ROOT / "EXAMPLE_ACCESS_CODE_GOES_HERE"

sur_nwb_conversion_table_path = PROJECT_ROOT / "agent_materials" / "sur_nwb_conversion_table.csv"
custom_to_sur_mapping_table_path = PROJECT_ROOT / "custom_to_sur_mapping_table.csv"
metadata_defaults_path = PROJECT_ROOT / "metadata_defaults.csv"

# Written by metadata_gap_audit after each conversion run
metadata_gap_report_log_path = PROJECT_ROOT / "logs" / "metadata_gap_report.md"

################
# computation config
#################

verbose = False

################
# logging
#################

log_path = PROJECT_ROOT / "logs" / "run.log"
