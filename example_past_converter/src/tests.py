"""End-to-end test: Tricolor demo session → SurLab."""

import logging
from pathlib import Path

import numpy as np

import sys

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
import config as cfg
from src.convert_session import convert_one_session, setup_logging
from src.surlab_io import build_session_filename, build_trial_table_filename


def test_demo_conversion():
    setup_logging(cfg.log_path)
    session_dir = Path(convert_one_session())

    data = np.load(
        session_dir / build_session_filename("GCaMP8m_traces", "data", "npz")
    )
    assert data["data"].ndim == 2
    assert data["data"].shape[0] > 1000

    ts = np.load(
        session_dir / build_session_filename("GCaMP8m_traces", "timestamps", "npz")
    )
    assert len(ts["timestamps"]) == data["data"].shape[0]

    trial_csv = session_dir / build_trial_table_filename("passive_trialInfo")
    assert trial_csv.is_file()
    logging.getLogger(__name__).info("test_demo_conversion passed")


if __name__ == "__main__":
    test_demo_conversion()
