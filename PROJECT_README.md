# replace_with_env_name

Converter: *[source format]* → SurLab standard layout.

## Installation

### Windows (recommended)

1. Clone this repository.
2. Double-click **`user_install_win.bat`** to create the conda environment.

### Any platform

```bash
git clone git@github.com:surlab/replace_with_env_name.git
cd replace_with_env_name
conda env create -f environment_cross_platform.yml
conda activate replace_with_env_name
```

Optional extra packages (if your source format needs them) are listed at the bottom of this README.

## Configuration

Edit **`config.py`** at the repo root:

- `dataset_id`, `animal_id`, `session_id`
- Paths under `EXAMPLE_SESSION_DIR_GOES_HERE/`, `EXAMPLE_SURFORMAT_DATASET_WILL_APPEAR_HERE/`, `EXAMPLE_ACCESS_CODE_GOES_HERE/`

Author **`custom_to_sur_mapping_table.csv`** for your source format. Use **`metadata_defaults.csv`** for strain, species, and other provenance the user supplies (not hardcoded in code). Use **`agent_materials/sur_nwb_conversion_table.csv`** as the SurLab target spec.

## Run

### Windows

Double-click **`main.bat`**.

### Command line

```bash
conda activate replace_with_env_name
python -m src.main
python -m src.tests
```

## Inputs

Place raw session files in:

```
EXAMPLE_SESSION_DIR_GOES_HERE/example_session/
```

Place reference access / preprocessing code in:

```
EXAMPLE_ACCESS_CODE_GOES_HERE/
```

## Outputs

SurLab dataset files are written under `EXAMPLE_SURFORMAT_DATASET_WILL_APPEAR_HERE/`, including `metadata_gap_report.md` when gaps exist.

After conversion, check that file and `logs/metadata_gap_report.md` for missing metadata.

## Quality control

QC outputs before downstream use. Use `src/explore_data.ipynb` to inspect tables and exported schema/metadata.

## Reference

Non-runnable Tricolor example: **`example_past_converter/`** (code architecture and `custom_to_sur_mapping_table.csv` sentinel).

## Optional dependencies

Add via conda/pip as needed for your source format, for example:

- `h5py` — HDF5 / DeepLabCut `.h5` pupil files
- `opencv-python` — video frame access
- `nwbio` / `pynwb` — only if exporting to NWB later

## Credit

Sur lab, MIT. Template by Gregg Heller.
