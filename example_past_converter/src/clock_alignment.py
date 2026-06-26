"""Imaging clock and MATLAB/voltage alignment."""

import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class ClockAlignment:
    imaging_timestamps_s: np.ndarray
    delta_matlab_to_imaging_s: float
    t_m0_s: float
    t_v0_s: float
    stim_table: pd.DataFrame

    def to_imaging_time(self, t_matlab_s):
        return np.asarray(t_matlab_s, dtype=float) + self.delta_matlab_to_imaging_s


def load_imaging_timestamps_s(xml_path):
    root = ET.parse(xml_path).getroot()
    times = [float(node.attrib["relativeTime"]) for node in root.iter("Frame")]
    if not times:
        raise ValueError(f"No Frame relativeTime in {xml_path}")
    return np.asarray(times, dtype=np.float64)


def load_stim_table(stim_npy_path):
    stim = np.load(stim_npy_path)
    stim = stim.reshape(-1, stim.shape[-1])
    columns = [
        "grating_orientation__degrees",
        "grating_spatial_frequency__cycles_per_degree",
        "stimulus_contrast",
        "onset_matlab_s",
    ]
    return pd.DataFrame(stim, columns=columns[: stim.shape[1]])


def compute_clock_alignment(imaging_xml, voltage_csv, stim_npy, ttl_threshold_v=4.9):
    imaging_timestamps_s = load_imaging_timestamps_s(imaging_xml)
    stim_table = load_stim_table(stim_npy)

    voltage = pd.read_csv(voltage_csv)
    time_col = "Time(ms)"
    signal_col = None
    for c in voltage.columns:
        if "input" in c.lower():
            signal_col = c
            break
    if signal_col is None:
        raise ValueError(f"No Input column in {voltage_csv}")

    t_ms = voltage[time_col].to_numpy(dtype=float)
    v = voltage[signal_col].to_numpy(dtype=float)
    rise_idx = np.where((v[:-1] < ttl_threshold_v) & (v[1:] >= ttl_threshold_v))[0] + 1
    if len(rise_idx) == 0:
        raise ValueError("No voltage TTL rises found")
    t_v0_s = t_ms[rise_idx[0]] / 1000.0
    t_m0_s = float(stim_table.iloc[0]["onset_matlab_s"])
    delta = t_v0_s - t_m0_s

    vis_onsets = stim_table["onset_matlab_s"].to_numpy(dtype=float)
    n = min(len(rise_idx), len(vis_onsets))
    v_on_imaging = (t_ms[rise_idx[:n]] / 1000.0) - delta
    diff_ms = (v_on_imaging - vis_onsets[:n]) * 1000.0
    logger.info(
        "Clock: tV0=%.4fs tM0=%.4fs delta=%.4fs | onset check n=%s mean=%.2fms",
        t_v0_s,
        t_m0_s,
        delta,
        n,
        float(np.nanmean(diff_ms)) if n else float("nan"),
    )

    return ClockAlignment(
        imaging_timestamps_s=imaging_timestamps_s,
        delta_matlab_to_imaging_s=delta,
        t_m0_s=t_m0_s,
        t_v0_s=t_v0_s,
        stim_table=stim_table,
    )


def detect_voltage_trials(voltage_csv, ttl_threshold_v=4.9):
    """Return rise and fall times in seconds (voltage hardware clock)."""
    voltage = pd.read_csv(voltage_csv)
    signal_col = [c for c in voltage.columns if "input" in c.lower()][0]
    t_s = voltage["Time(ms)"].to_numpy(dtype=float) / 1000.0
    v = voltage[signal_col].to_numpy(dtype=float)
    rise_idx = np.where((v[:-1] < ttl_threshold_v) & (v[1:] >= ttl_threshold_v))[0] + 1
    fall_idx = np.where((v[:-1] >= ttl_threshold_v) & (v[1:] < ttl_threshold_v))[0] + 1
    return t_s[rise_idx], t_s[fall_idx]
