"""Convert one Tricolor example_session into SurLab layout."""

import logging
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
import config as cfg
from src.beh_series import export_pupil_beh_series, export_wheel_beh_series
from src.clock_alignment import compute_clock_alignment
from src.discover_session import discover_session
from src.passive_trials import write_passive_trial_info
from src.session_info import write_session_info_files
from src.traces_streams import export_traces_streams
from src.surlab_io import cleanup_legacy_session_filenames
from src.validate_surlab import validate_session


def setup_logging(log_path):
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_path, mode="w"),
            logging.StreamHandler(),
        ],
        force=True,
    )


def session_date_from_session_id(session_id):
    """20260204-gratings -> 2026-02-04"""
    date_part = session_id.split("-")[0]
    if len(date_part) == 8 and date_part.isdigit():
        return f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}"
    raise ValueError(f"Cannot parse date from session_id: {session_id}")


def convert_one_session(
    raw_session_root=None,
    output_dataset_root=None,
    dataset_id=None,
    animal_id=None,
    session_id=None,
    dataset_config_path=None,
):
    raw_session_root = Path(raw_session_root or cfg.raw_session_root)
    output_dataset_root = Path(output_dataset_root or cfg.output_dataset_root)
    dataset_id = dataset_id or cfg.dataset_id
    animal_id = animal_id or cfg.animal_id
    session_id = session_id or cfg.session_id
    dataset_config_path = Path(dataset_config_path or cfg.dataset_config_path)

    logger = logging.getLogger(__name__)
    session_paths = discover_session(raw_session_root)
    clock = compute_clock_alignment(
        session_paths.imaging_xml,
        session_paths.voltage_csv,
        session_paths.stim_npy,
        ttl_threshold_v=cfg.voltage_ttl_threshold_v,
    )

    session_date = session_date_from_session_id(session_id)
    session_dir = write_session_info_files(
        output_dataset_root,
        dataset_id,
        animal_id,
        session_id,
        session_date,
        dataset_config_path,
    )

    export_traces_streams(session_paths, session_dir, clock)
    export_pupil_beh_series(session_paths, session_dir, clock)
    export_wheel_beh_series(session_paths, session_dir, clock)
    write_passive_trial_info(
        session_dir,
        session_paths.voltage_csv,
        clock.stim_table,
        clock,
        cfg.voltage_ttl_threshold_v,
    )
    cleanup_legacy_session_filenames(session_dir, dataset_id, animal_id, session_id)
    validate_session(output_dataset_root, dataset_id, animal_id, session_id)
    logger.info("Conversion complete: %s", session_dir)
    return session_dir


def main():
    setup_logging(cfg.log_path)
    try:
        convert_one_session()
    except Exception:
        logging.exception("Conversion failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
