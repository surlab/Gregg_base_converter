"""Export GCaMP8m and Neuropil trace streams (SurLab stage 3)."""

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

CLASSIFICATION_KEYS = ["mCherry", "mNeptune", "tdTomato"]


def _roi_classification_labels(classification_npy_path, n_rois):
    labels = np.full(n_rois, "unclassified", dtype=object)
    if classification_npy_path is None or not classification_npy_path.is_file():
        return labels
    cls_dict = np.load(classification_npy_path, allow_pickle=True).item()
    bool_matrix = np.column_stack([cls_dict[k] for k in CLASSIFICATION_KEYS])
    has_any = bool_matrix.any(axis=1)
    n_classified = bool_matrix.shape[0]
    # Align to trailing ROIs when classification count < suite2p ROI count
    start = n_rois - n_classified
    if start < 0:
        start = 0
    for i in range(min(n_classified, n_rois - start)):
        if has_any[i]:
            labels[start + i] = CLASSIFICATION_KEYS[bool_matrix[i].argmax()]
    return labels


def _build_roi_metadata(stat, iscell, fluorophore_labels):
    rows = []
    for i, s in enumerate(stat):
        med = s["med"]
        rows.append(
            {
                "roi_ID": i,
                "roi_x_coordinate": float(np.min(s["xpix"])),
                "roi_y_coordinate": float(np.min(s["ypix"])),
                "roi_center_x": float(med[1]),
                "roi_center_y": float(med[0]),
                "iscell": int(iscell[i, 0]) if iscell.ndim > 1 else int(iscell[i]),
                "fluorophore_class": str(fluorophore_labels[i]),
            }
        )
    return pd.DataFrame(rows)


def _write_trace_stream(
    session_dir,
    datatype_id,
    data_time_by_roi,
    imaging_timestamps_s,
    sample_hz,
    indicator,
    roi_metadata,
):
    paths = stream_paths(session_dir, datatype_id)
    n_time, n_roi = data_time_by_roi.shape
    save_npz_array(paths["data"], data_time_by_roi)
    save_timestamps_npz(paths["timestamps"], imaging_timestamps_s)
    schema = {
        "data_unit_measurement": "fluorescence__a.u.",
        "X_dim": "time",
        "Y_dim": "ROI",
        "X_size": int(n_time),
        "Y_size": int(n_roi),
        "sample_frequency__Hz": float(sample_hz),
        "indicator": indicator,
        "detection_software": "Suite2p",
    }
    save_schema_json(paths["schema"], schema)
    save_metadata_csv(paths["metadata"], roi_metadata)
    logger.info("Stream %s: (%s, %s)", datatype_id, n_time, n_roi)


def export_traces_streams(session_paths, session_dir, clock):
    f_raw = np.load(session_paths.f_npy)
    fneu_raw = np.load(session_paths.fneu_npy)
    stat = np.load(session_paths.stat_npy, allow_pickle=True)
    iscell = np.load(session_paths.iscell_npy)
    ops = np.load(session_paths.ops_npy, allow_pickle=True).item()
    sample_hz = float(ops.get("fs", np.nan))

    n_roi = f_raw.shape[0]
    fluor = _roi_classification_labels(session_paths.classification_npy, n_roi)
    roi_metadata = _build_roi_metadata(stat, iscell, fluor)

    imaging_ts = clock.imaging_timestamps_s
    f_time_roi = np.asarray(f_raw.T, dtype=np.float64)
    fneu_time_roi = np.asarray(fneu_raw.T, dtype=np.float64)
    if f_time_roi.shape[0] != len(imaging_ts):
        n = min(f_time_roi.shape[0], len(imaging_ts))
        logger.warning(
            "Truncating frames: F has %s, xml has %s — using %s",
            f_time_roi.shape[0],
            len(imaging_ts),
            n,
        )
        f_time_roi = f_time_roi[:n, :]
        fneu_time_roi = fneu_time_roi[:n, :]
        imaging_ts = imaging_ts[:n]

    _write_trace_stream(
        session_dir,
        "GCaMP8m_traces",
        f_time_roi,
        imaging_ts,
        sample_hz,
        "GCaMP8m",
        roi_metadata,
    )
    _write_trace_stream(
        session_dir,
        "Neuropil_traces",
        fneu_time_roi,
        imaging_ts,
        sample_hz,
        "neuropil",
        roi_metadata,
    )
