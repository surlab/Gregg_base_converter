"""Build passive_trialInfo CSV aligned to imaging time zero."""

import logging
from pathlib import Path

import pandas as pd

from src.clock_alignment import detect_voltage_trials
from src.surlab_io import build_trial_table_filename

logger = logging.getLogger(__name__)


def _trials_from_voltage_and_stim(voltage_csv, stim_table, clock, ttl_threshold_v):
    rises_s, falls_s = detect_voltage_trials(voltage_csv, ttl_threshold_v)
    rises_imaging = clock.to_imaging_time(rises_s)
    falls_imaging = clock.to_imaging_time(falls_s)

    n_stim = len(stim_table)
    trials = []

    for idx in range(n_stim):
        stim_row = stim_table.iloc[idx]
        if idx < len(rises_imaging):
            onset = float(rises_imaging[idx])
            if idx < len(falls_imaging):
                offset = float(falls_imaging[idx])
            elif idx + 1 < len(rises_imaging):
                offset = float(rises_imaging[idx + 1])
            else:
                offset = onset + 1.0
        else:
            onset = float(clock.to_imaging_time(stim_row["onset_matlab_s"]))
            if idx + 1 < n_stim:
                next_on = float(
                    clock.to_imaging_time(stim_table.iloc[idx + 1]["onset_matlab_s"])
                )
                offset = next_on
            else:
                offset = onset + 1.0

        start = onset
        stop = max(offset, onset + 0.01)
        trials.append(
            {
                "start_time__s": start,
                "stop_time__s": stop,
                "stimulus_onset__s": onset,
                "stimulus_offset__s": offset,
                "grating_orientation__degrees": float(
                    stim_row["grating_orientation__degrees"]
                ),
                "grating_spatial_frequency__cycles_per_degree": float(
                    stim_row["grating_spatial_frequency__cycles_per_degree"]
                ),
                "stimulus_contrast": float(stim_row["stimulus_contrast"]),
            }
        )

    if len(rises_imaging) < n_stim:
        logger.warning(
            "Voltage assigned %s rises; stim_file has %s — filled remainder from stim onsets",
            len(rises_imaging),
            n_stim,
        )
    return pd.DataFrame(trials)


def write_passive_trial_info(
    session_dir,
    voltage_csv,
    stim_table,
    clock,
    ttl_threshold_v,
    trial_datatype_id="passive_trialInfo",
):
    session_dir = Path(session_dir)
    df = _trials_from_voltage_and_stim(
        voltage_csv, stim_table, clock, ttl_threshold_v
    )
    out_path = session_dir / build_trial_table_filename(trial_datatype_id)
    df.to_csv(out_path, index=False)
    logger.info("Wrote %s (%s trials)", out_path.name, len(df))
    return out_path
