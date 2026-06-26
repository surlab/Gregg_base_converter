"""Validate exported SurLab session against sur_nwb_conversion_table rules."""

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from src.surlab_io import build_session_filename, build_trial_table_filename

logger = logging.getLogger(__name__)

PASSIVE_TRIAL_ID = "passive_trialInfo"


def _load_npz(path, key):
    with np.load(path, allow_pickle=False) as z:
        return z[key]


def validate_stream(session_dir, datatype_id):
    errors = []
    session_dir = Path(session_dir)
    data_path = session_dir / build_session_filename(datatype_id, "data", "npz")
    ts_path = session_dir / build_session_filename(datatype_id, "timestamps", "npz")
    schema_path = session_dir / build_session_filename(datatype_id, "schema", "json")
    meta_path = session_dir / build_session_filename(datatype_id, "metadata", "csv")

    for p in (data_path, ts_path, schema_path, meta_path):
        if not p.is_file():
            errors.append(f"Missing file: {p.name}")

    if errors:
        return errors

    data = _load_npz(data_path, "data")
    timestamps = _load_npz(ts_path, "timestamps")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    meta = pd.read_csv(meta_path)

    n_time, n_unit = data.shape
    if schema.get("X_size") != n_time:
        errors.append(f"{datatype_id}: X_size {schema.get('X_size')} != {n_time}")
    if schema.get("Y_size") != n_unit:
        errors.append(f"{datatype_id}: Y_size {schema.get('Y_size')} != {n_unit}")
    if n_time > 0 and len(meta) != n_unit:
        errors.append(
            f"{datatype_id}: metadata rows {len(meta)} != Y_size {n_unit}"
        )
    if n_time > 0 and len(timestamps) != n_time:
        errors.append(
            f"{datatype_id}: timestamps len {len(timestamps)} != n_time {n_time}"
        )
    if len(timestamps) > 1 and np.any(np.diff(timestamps) < 0):
        errors.append(f"{datatype_id}: timestamps not monotonic")
    return errors


def validate_session(output_dataset_root, dataset_id, animal_id, session_id):
    output_dataset_root = Path(output_dataset_root)
    session_dir = output_dataset_root / f"{animal_id}_{session_id}"
    all_errors = []

    info_path = output_dataset_root / f"sessionInfo_{dataset_id}.csv"
    if not info_path.is_file():
        all_errors.append(f"Missing {info_path.name}")
    else:
        info = pd.read_csv(info_path)
        if "zero_time" not in info.columns:
            all_errors.append("sessionInfo missing zero_time")

    single = session_dir / "sessionInfo_single_session.csv"
    if not single.is_file():
        all_errors.append("Missing sessionInfo_single_session.csv")

    for stream in [
        "GCaMP8m_traces",
        "Neuropil_traces",
        "pupil_behTSeries",
        "wheel_behTSeries",
    ]:
        all_errors.extend(validate_stream(session_dir, stream))

    trial_name = build_trial_table_filename(PASSIVE_TRIAL_ID)
    if not (session_dir / trial_name).is_file():
        all_errors.append(f"Missing {trial_name}")

    if all_errors:
        for e in all_errors:
            logger.error("Validation: %s", e)
        raise ValueError(f"Validation failed with {len(all_errors)} error(s)")
    logger.info("Validation passed for session %s_%s", animal_id, session_id)
    return all_errors


def main():
    import sys

    _ROOT = Path(__file__).resolve().parent.parent
    if str(_ROOT) not in sys.path:
        sys.path.insert(0, str(_ROOT))
    import config as cfg
    from src.convert_session import setup_logging

    setup_logging(cfg.log_path)
    try:
        validate_session(
            cfg.output_dataset_root,
            cfg.dataset_id,
            cfg.animal_id,
            cfg.session_id,
        )
    except ValueError:
        sys.exit(1)


if __name__ == "__main__":
    main()
