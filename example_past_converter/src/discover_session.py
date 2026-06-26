"""Discover raw Tricolor session files under example_session."""

import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class SessionPaths:
    suite2p_dir: Path
    f_npy: Path
    fneu_npy: Path
    iscell_npy: Path
    stat_npy: Path
    ops_npy: Path
    classification_npy: Path
    imaging_xml: Path
    voltage_csv: Path
    stim_npy: Path
    wheel_npy: Path
    pupil_csv: Path
    pupil_h5: Path
    pupil_tstamp: Path
    mat_file: Path


def _is_readable(path):
    path = Path(path)
    try:
        return path.is_file() and path.stat().st_size > 0
    except OSError:
        return False


def _first_match(root, pattern):
    matches = sorted(root.glob(pattern))
    for match in matches:
        if _is_readable(match):
            return match
    return None


def discover_session(raw_root):
    """
    Find required files under example_session (flexible layout).

    Expects date folder (e.g. 20260204) with suite2p and voltage/xml.
    """
    raw_root = Path(raw_root)
    if not raw_root.is_dir():
        raise FileNotFoundError(f"Raw session root not found: {raw_root}")

    date_dirs = [d for d in raw_root.iterdir() if d.is_dir() and d.name.isdigit()]
    if not date_dirs:
        raise FileNotFoundError(f"No date folder under {raw_root}")
    date_dir = sorted(date_dirs)[0]
    logger.info("Using imaging date folder %s", date_dir.name)

    suite2p = date_dir / "suite2p" / "plane0"
    f_npy = suite2p / "F.npy"
    fneu_npy = suite2p / "Fneu.npy"
    for p in (f_npy, fneu_npy):
        if not p.is_file():
            raise FileNotFoundError(f"Missing {p}")

    imaging_xml = _first_match(date_dir, "*.xml")
    voltage_csv = _first_match(date_dir, "*VoltageRecording*.csv")
    if imaging_xml is None or voltage_csv is None:
        raise FileNotFoundError("Missing imaging XML or voltage CSV")

    stim_npy = _first_match(raw_root, "**/stim_file.npy")
    wheel_npy = _first_match(raw_root, "**/wheel_file.npy")
    pupil_csv = _first_match(raw_root, "**/*DLC*.csv")
    pupil_h5 = _first_match(raw_root, "**/*DLC*.h5")
    pupil_tstamp = _first_match(raw_root, "**/*_tStamp.txt")
    mat_file = _first_match(raw_root, "**/*.mat")

    classification = date_dir / "cellpose" / "classification.npy"
    if not classification.is_file():
        classification = None

    paths = SessionPaths(
        suite2p_dir=suite2p,
        f_npy=f_npy,
        fneu_npy=fneu_npy,
        iscell_npy=suite2p / "iscell.npy",
        stat_npy=suite2p / "stat.npy",
        ops_npy=suite2p / "ops.npy",
        classification_npy=classification,
        imaging_xml=imaging_xml,
        voltage_csv=voltage_csv,
        stim_npy=stim_npy,
        wheel_npy=wheel_npy,
        pupil_csv=pupil_csv,
        pupil_h5=pupil_h5,
        pupil_tstamp=pupil_tstamp,
        mat_file=mat_file,
    )
    for name, p in [
        ("stim", stim_npy),
        ("wheel", wheel_npy),
        ("pupil_csv", pupil_csv),
        ("pupil_tstamp", pupil_tstamp),
    ]:
        if p is None:
            logger.warning("Optional path not found: %s", name)
        else:
            logger.info("Found %s: %s", name, p)
    return paths
