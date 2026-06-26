"""Build sessionInfo CSV files (SurLab stage 1)."""

import logging
from pathlib import Path

import pandas as pd

from src.surlab_io import load_dataset_config

logger = logging.getLogger(__name__)

ZERO_TIME_STREAM = "GCaMP8m_traces"

STREAM_FLAGS = [
    "GCaMP8m_traces",
    "Neuropil_traces",
    "pupil_behTSeries",
    "wheel_behTSeries",
    "passive_trialInfo",
]


def build_session_info_row(dataset_config, animal_id, session_id, session_date):
    row = {
        "institution": dataset_config["institution"],
        "lab": dataset_config["lab"],
        "experimenter": dataset_config["experimenter"],
        "animal_ID": animal_id,
        "session_ID": session_id,
        "session_date": session_date,
        "species": dataset_config["species"],
        "sex": dataset_config.get("sex", "U"),
        "age__days": dataset_config.get("age__days", ""),
        "strain": dataset_config["strain"],
        "zero_time": ZERO_TIME_STREAM,
        "area": dataset_config.get("area", ""),
        "condition": dataset_config.get("condition", ""),
        "related_publication": dataset_config.get("related_publication", ""),
    }
    for stream in STREAM_FLAGS:
        row[stream] = 1
    row["spikeTimes"] = 0
    row["lfp"] = 0
    row["spikeWaves"] = 0
    row["behEvents"] = 0
    return row


def write_session_info_files(
    output_dataset_root,
    dataset_id,
    animal_id,
    session_id,
    session_date,
    dataset_config_path,
):
    output_dataset_root = Path(output_dataset_root)
    dataset_config = load_dataset_config(dataset_config_path)
    row = build_session_info_row(
        dataset_config, animal_id, session_id, session_date
    )
    df = pd.DataFrame([row])

    dataset_csv = output_dataset_root / f"sessionInfo_{dataset_id}.csv"
    df.to_csv(dataset_csv, index=False)
    logger.info("Wrote %s", dataset_csv)

    session_dir = output_dataset_root / f"{animal_id}_{session_id}"
    session_dir.mkdir(parents=True, exist_ok=True)
    single = session_dir / "sessionInfo_single_session.csv"
    df.to_csv(single, index=False)
    logger.info("Wrote %s", single)
    return session_dir
