"""Read/write SurLab filenames and file formats."""

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def build_session_filename(datatype_id, role, ext):
    """
    Session-folder filename: <datatypeID>_<role>.<ext>

    datasetID, animal_ID, and session_ID live in parent folder names only.
    """
    return f"{datatype_id}_{role}.{ext}"


def build_trial_table_filename(trial_datatype_id="passive_trialInfo"):
    """Trial table CSV inside session folder (short name)."""
    return f"{trial_datatype_id}.csv"


def session_folder_name(animal_id, session_id):
    return f"{animal_id}_{session_id}"


def save_npz_array(path, array, key="data"):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, **{key: np.asarray(array)})
    logger.info("Wrote %s shape %s", path.name, np.asarray(array).shape)


def save_timestamps_npz(path, timestamps_s):
    save_npz_array(path, timestamps_s, key="timestamps")


def save_schema_json(path, schema_dict):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(schema_dict, f, indent=2)
    logger.info("Wrote %s", path.name)


def save_metadata_csv(path, dataframe):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(path, index=False)
    logger.info("Wrote %s (%s rows)", path.name, len(dataframe))


def load_dataset_config(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def cleanup_legacy_session_filenames(session_dir, dataset_id, animal_id, session_id):
    """Remove pre-short-name files that repeated dataset/session IDs in each filename."""
    session_dir = Path(session_dir)
    suffix = f"_{dataset_id}_{animal_id}_{session_id}"
    removed = 0
    for path in session_dir.iterdir():
        if path.is_file() and suffix in path.stem:
            path.unlink()
            removed += 1
            logger.info("Removed legacy file %s", path.name)
    if removed:
        logger.info("Removed %s legacy long-named file(s)", removed)


def stream_paths(session_dir, datatype_id):
    """Paths for one stream inside a session folder (short filenames)."""
    session_dir = Path(session_dir)
    return {
        "data": session_dir / build_session_filename(datatype_id, "data", "npz"),
        "timestamps": session_dir
        / build_session_filename(datatype_id, "timestamps", "npz"),
        "schema": session_dir / build_session_filename(datatype_id, "schema", "json"),
        "metadata": session_dir
        / build_session_filename(datatype_id, "metadata", "csv"),
    }
