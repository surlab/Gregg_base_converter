"""Export behavioral time series: pupil (native DLC) and wheel placeholder."""

import logging

import numpy as np
import pandas as pd

from src.surlab_io import (
    save_metadata_csv,
    save_npz_array,
    save_schema_json,
    save_timestamps_npz,
    stream_paths,
)

logger = logging.getLogger(__name__)


def _read_dlc_csv(pupil_csv_path):
    raw = pd.read_csv(pupil_csv_path)
    raw.columns = raw.iloc[0].astype(str) + "_" + raw.iloc[1].astype(str)
    pupil = raw.iloc[2:].reset_index(drop=True)
    return pupil.astype(float)


def _read_dlc_h5(pupil_h5_path):
    df = pd.read_hdf(pupil_h5_path)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [
            f"{a}_{b}".strip("_") for a, b in df.columns.to_flat_index()
        ]
    return df.astype(float)


def _pupil_derived_columns(pupil):
    out = pupil.copy()
    if all(c in out.columns for c in ["vright_x", "vright_y", "vdown_x", "vdown_y"]):
        out["vertical_diameter_px"] = np.sqrt(
            (out["vright_x"] - out["vdown_x"]) ** 2 + (out["vright_y"] - out["vdown_y"]) ** 2
        )
    if all(c in out.columns for c in ["hleft_x", "hleft_y", "hright_x", "hright_y"]):
        out["horizontal_diameter_px"] = np.sqrt(
            (out["hleft_x"] - out["hright_x"]) ** 2 + (out["hleft_y"] - out["hright_y"]) ** 2
        )
    if all(c in out.columns for c in ["c1_x", "c1_y", "c8_x", "c8_y"]):
        out["clock1_diameter_px"] = np.sqrt(
            (out["c1_x"] - out["c8_x"]) ** 2 + (out["c1_y"] - out["c8_y"]) ** 2
        )
    if all(c in out.columns for c in ["c4_x", "c4_y", "c11_x", "c11_y"]):
        out["clock4_diameter_px"] = np.sqrt(
            (out["c4_x"] - out["c11_x"]) ** 2 + (out["c4_y"] - out["c11_y"]) ** 2
        )
    return out


def _load_pupil_timestamps_s(tstamp_path, clock):
    """Native DLC tStamp, shifted to imaging zero via MATLAB alignment offset."""
    ts = np.loadtxt(tstamp_path, dtype=np.float64)
    if ts.ndim == 0:
        ts = np.array([float(ts)])
    # Treat tStamp as MATLAB-session seconds; align to imaging reference
    ts_imaging = clock.to_imaging_time(ts)
    return ts_imaging


def export_pupil_beh_series(session_paths, session_dir, clock):
    pupil_h5 = getattr(session_paths, "pupil_h5", None)
    pupil = None
    if session_paths.pupil_csv is not None:
        pupil = _read_dlc_csv(session_paths.pupil_csv)
    elif pupil_h5 is not None:
        pupil = _read_dlc_h5(pupil_h5)

    if pupil is None:
        logger.warning(
            "Pupil DLC CSV/H5 not available locally (Dropbox may be online-only). "
            "Writing empty pupil_behTSeries placeholder."
        )
        _write_empty_beh_series(
            session_dir, "pupil_behTSeries", feature_label="pupil_placeholder"
        )
        return

    if session_paths.pupil_tstamp is None:
        raise FileNotFoundError("Pupil tStamp required when DLC data is present")

    pupil = _pupil_derived_columns(pupil)
    timestamps_s = _load_pupil_timestamps_s(session_paths.pupil_tstamp, clock)

    feature_cols = [c for c in pupil.columns]
    n_frames = len(pupil)
    if len(timestamps_s) != n_frames:
        n = min(len(timestamps_s), n_frames)
        logger.warning(
            "Pupil tStamp (%s) vs DLC rows (%s) — using %s",
            len(timestamps_s),
            n_frames,
            n,
        )
        timestamps_s = timestamps_s[:n]
        pupil = pupil.iloc[:n]

    data = pupil[feature_cols].to_numpy(dtype=np.float64)
    metadata = pd.DataFrame(
        {
            "feature_ID": range(len(feature_cols)),
            "feature_label": feature_cols,
        }
    )

    datatype_id = "pupil_behTSeries"
    paths = stream_paths(session_dir, datatype_id)
    save_npz_array(paths["data"], data)
    save_timestamps_npz(paths["timestamps"], timestamps_s)
    dt = np.median(np.diff(timestamps_s)) if len(timestamps_s) > 1 else np.nan
    sample_hz = 1.0 / dt if dt > 0 else np.nan
    schema = {
        "data_unit_measurement": "mixed__see_metadata",
        "X_dim": "time",
        "Y_dim": "features",
        "X_size": int(data.shape[0]),
        "Y_size": int(data.shape[1]),
        "sample_frequency__Hz": float(sample_hz),
    }
    save_schema_json(paths["schema"], schema)
    save_metadata_csv(paths["metadata"], metadata)
    logger.info("pupil_behTSeries: %s frames x %s features", data.shape[0], data.shape[1])


def _write_empty_beh_series(session_dir, datatype_id, feature_label):
    paths = stream_paths(session_dir, datatype_id)
    data = np.zeros((0, 1), dtype=np.float64)
    timestamps_s = np.zeros(0, dtype=np.float64)
    metadata = pd.DataFrame(
        {"feature_ID": [0], "feature_label": [feature_label]}
    )
    save_npz_array(paths["data"], data)
    save_timestamps_npz(paths["timestamps"], timestamps_s)
    schema = {
        "data_unit_measurement": "mixed__see_metadata",
        "X_dim": "time",
        "Y_dim": "features",
        "X_size": 0,
        "Y_size": 1,
        "sample_frequency__Hz": 0.0,
    }
    save_schema_json(paths["schema"], schema)
    save_metadata_csv(paths["metadata"], metadata)


def export_wheel_beh_series(session_paths, session_dir, clock):
    datatype_id = "wheel_behTSeries"
    paths = stream_paths(session_dir, datatype_id)

    wheel = None
    if session_paths.wheel_npy and session_paths.wheel_npy.is_file():
        wheel = np.load(session_paths.wheel_npy)

    if wheel is None or wheel.size == 0:
        logger.info("wheel_behTSeries: empty placeholder")
        _write_empty_beh_series(
            session_dir, datatype_id, feature_label="wheel_speed_native"
        )
        return
    else:
        wheel_df = pd.DataFrame(wheel)
        t_matlab = wheel_df.iloc[:, 0].to_numpy(dtype=float)
        speed = wheel_df.iloc[:, 1].to_numpy(dtype=float)
        timestamps_s = clock.to_imaging_time(t_matlab)
        data = speed.reshape(-1, 1)
        metadata = pd.DataFrame(
            {"feature_ID": [0], "feature_label": ["wheel_speed_native"]}
        )
        save_npz_array(paths["data"], data)
        save_timestamps_npz(paths["timestamps"], timestamps_s)
        dt = np.median(np.diff(timestamps_s)) if len(timestamps_s) > 1 else np.nan
        sample_hz = float(1.0 / dt) if dt > 0 else 0.0
        schema = {
            "data_unit_measurement": "speed__native_units",
            "X_dim": "time",
            "Y_dim": "features",
            "X_size": int(data.shape[0]),
            "Y_size": int(data.shape[1]),
            "sample_frequency__Hz": sample_hz,
        }
        save_schema_json(paths["schema"], schema)
        save_metadata_csv(paths["metadata"], metadata)
