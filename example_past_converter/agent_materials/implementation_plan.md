# Implementation plan: Tricolor → SurLab converter

Preserved specification for converting `demo_data/tricolor_projections/example_session/` raw inputs into SurLab layout under `demo_data/tricolor_projections/`.

## Locked specifications

| Item | Value |
|------|--------|
| `datasetID` | `tricolor_projections` |
| `animal_ID` | `exp101-a1` |
| `session_ID` | `20260204-gratings` |
| Session folder | `exp101-a1_20260204-gratings/` |
| `zero_time` | `GCaMP8m_traces` (imaging XML frame 0) |
| Time base | All streams + `passive_trialInfo` in **seconds relative to imaging t = 0** |
| MATLAB→imaging offset | `delta_s = tV0_s - tM0_s` → `t_imaging = t_matlab + delta_s` (do **not** shift imaging timestamps) |
| Resampling | None — native rates only |
| Trace streams | `GCaMP8m_traces` (raw `F`), `Neuropil_traces` (raw `Fneu`) |
| Indicator in schema | GCaMP8m |
| `strain` | `flex-GCaMP8m x CamkII-Cre` |
| `species` | `Mus musculus` |
| `experimenter` | Sofie Ahrlund Richter |
| `institution` / `lab` | MIT / Mriganka Sur |
| ROIs | All suite2p ROIs; metadata: `iscell`, tricolor label, coords from `stat` |
| Pupil | `pupil_behTSeries` — all DLC traces + keypoints; native `*_tStamp.txt` |
| Wheel | `wheel_behTSeries` — valid empty shell if no data |
| Trials | `passive_trialInfo_*` filename stem; TTL + stim_file (Sofie-style gap fill) |
| Passive trials | No operant columns; timing + grating params |
| Export arrays | `.npz`; schema `.json`; metadata `.csv` |
| Scope | SurLab only + validation (no NWB) |

## Target directory layout

```
demo_data/tricolor_projections/
├── dataset_config.json
├── sessionInfo_tricolor_projections.csv
├── example_session/                       # raw inputs (read-only)
└── exp101-a1_20260204-gratings/
    ├── sessionInfo_single_session.csv
    ├── GCaMP8m_traces_data_...npz
    ├── GCaMP8m_traces_timestamps_...npz
    ├── GCaMP8m_traces_schema_...json
    ├── GCaMP8m_traces_metadata_...csv
    ├── Neuropil_traces_*  (same quartet)
    ├── pupil_behTSeries_*
    ├── wheel_behTSeries_*
    └── passive_trialInfo.csv
```

## Architecture (flat `src/`)

| Module | Responsibility |
|--------|----------------|
| `default_config.py` | Paths, `datasetID`, output root |
| `discover_session.py` | Glob raw paths under `example_session/` |
| `clock_alignment.py` | XML times; voltage TTL; `delta_s`; stim_file |
| `session_info.py` | sessionInfo CSVs + stream flags |
| `traces_streams.py` | F/Fneu → SurLab traces |
| `beh_series.py` | Pupil DLC + wheel placeholder |
| `passive_trials.py` | passive_trialInfo table |
| `surlab_io.py` | Filenames, `.npz`/`.json`/`.csv` writers |
| `validate_surlab.py` | Checks vs `conversion_table.csv` |
| `convert_session.py` | CLI orchestrator |

## Clock policy

- **Imaging:** `imaging_timestamps_s` = XML `relativeTime` per frame (unchanged; t=0 at scan start).
- **Trials / MATLAB-derived times:** `t_imaging = t_matlab + (tV0_s - tM0_s)`.
- **No resampling** (no 20 Hz upsampling from reference script).

## Array layout

- Canonical SurLab: axis 0 = time, axis 1 = ROIs/features.
- Suite2p `(n_roi, n_time)` → transpose on ingest.
- Schema: `X_dim=time`, `Y_dim=ROI` or `features`; `X_size=n_time`, `Y_size=n_units`.

## Trial logic (passive)

1. Detect voltage TTL rises/falls (4.9 V threshold).
2. Assign stim_file direction/contrast per Sofie loop when pulses exist.
3. If fewer voltage trials than `stim_file` rows, fill from `stim_file` onset column + `delta_s`.
4. Columns: `start_time__s`, `stop_time__s`, `stimulus_onset__s`, `stimulus_offset__s`, `grating_orientation__degrees`, contrast-related fields from stim cols.

## Out of scope (v1)

- NWB export, F_chan2 separate streams, resampled wide CSV, experimentDesc.pdf, spike times, LFP, behEvents.

## Implementation order

1. Config + mapping tables + root `conversion_table.csv`
2. Discovery + clock alignment
3. `surlab_io` + sessionInfo
4. Traces → beh series → passive trials
5. Validation + `run_convert_demo.bat` + tests
