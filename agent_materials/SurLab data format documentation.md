# Sur Lab standardized data format

The SurLab data format provides a standardized framework for storing and analyzing preprocessed neurophysiology data. It is designed to maximize accessibility and ease of use, relying on a flat and easily parsable organization.

## **Naming conventions (summary)**

- **Case and style**
  - **Tabular field names** (CSV column headers; keys in `.json` schema that describe the same semantics as those tables): **`snake_case`**. Use **full words** where applicable (**session**, **stimulus**, **behavioral**, **sample_frequency**, **grid_location**, **clustering_algorithm**, **primary_channel**, **data_unit_measurement**, etc.). Identifier columns end with a **capital `ID`**: **`_ID`** after an underscore (e.g. **`animal_ID`**, **`session_ID`**, **`roi_ID`**), not glued forms like `animalID` or lowercase `animal_id`.
  - **Standard abbreviations** in names or labels use their usual **capitalization** (e.g. **LFP**, **ROI**, **PMT**, **FOV**, **2P** for two-photon, **SNR**, **TTL**). When an abbreviation appears inside a **snake_case** name, keep the abbreviation’s letters capital (e.g. `LFP` as a modality token in documentation or column values).
  - **Datatype IDs** and **filename stems** (e.g. **`spikeTimes`**, **`sessionInfo_<datasetID>.csv`**, **`trialInfo.csv`**) may use **camelCase**; this is intentional and separate from tabular field naming.
  - **Schema axis keys** keep **`X`** and **`Y`** capital; use **`X_dim`**, **`Y_dim`**, **`X_size`**, **`Y_size`**, **`X_idx`**, **`Y_idx`** (underscore after the axis letter).
- **Micrometers** in machine-readable names use ASCII **`um`** (not the µ symbol), e.g. `depth__um`.
- **`sessionInfo.csv`**: Prefer **session-level** metadata here rather than relying only on `.json` schema files (schema may remain for interchange). For columns that replace former schema fields, **do not** put unit suffixes in the **header**; encode the physical quantity in **cell values** using the **`base__unit`** text pattern where needed (e.g. `amplitude__V`). **Exceptions**: **`session_date`** is a plain calendar column (no dunder; values **`YYYY-MM-DD`**); **`age__days`** is the column name for age in days (numeric). Optional **calibration** columns (e.g. laser/PMT/Pockels) are **recommended** when hardware readouts are arbitrary until the user supplies a conversion.
- **`trialInfo.csv`**: Use **dunder + unit** in **column headers** for physical quantities (e.g. `tone_frequency__Hz`); **numeric** cell values only.
- **Dimension sizes** (`X_size`, `Y_size`, etc.): do **not** add misleading suffixes such as `__count` or `__samples`; describe meaning in prose.
- **Sampling rate** (schema or duplicated in session info): **`sample_frequency__Hz`** (float, Hz).

## **Conversion table (`sur_nwb_conversion_table.csv`)**

Machine-readable mapping from SurLab files and fields to NWB targets lives in **`sur_nwb_conversion_table.csv`** at the project root. Downstream tooling should treat that file as the spec; this document is the human-readable companion.

Each converter also authors **`custom_to_sur_mapping_table.csv`** at the repo root, mapping the **source** format into SurLab artifacts (see `example_past_converter/custom_to_sur_mapping_table.csv` for a Tricolor example).

**Filename and condition placeholders** (same spelling as in the table):

| Token | Meaning |
| :---- | :---- |
| `<datasetID>` | Dataset folder name |
| `<animal_ID>` | From `sessionInfo` |
| `<session_ID>` | From `sessionInfo` |
| `<datatypeID>` | **Full stream datatype ID** for one recording (optional prefix + base ID). Substitute separately for each stream present in the session (e.g. `GCaMP7f_traces`, `pupil_behTSeries`). Used in `surlab_filename`, `requirement_condition` (`if_datatype_present:<datatypeID>`), and per-stream `sessionInfo` column headers. |

**Stages** in the table: **1** session metadata; **2** spike times; **3** optical **`traces`** (one block per `<datatypeID>` stream); **4** **`behTSeries`** (one block per stream); **5** **`trialInfo`**; later stages (e.g. LFP) numbered with gaps as added.

NWB target columns in the table may be marked **SPECULATIVE** until validated against real data and the official NWB validator.

## **Data organization**

All data for each project (a **dataset**) is saved in a single folder named with a short **datasetID** (e.g. `Astro_seqBias` for astrocytes calcium recordings during a sequential go/no-go task). The format handles several **dataTypes**, including optical physiology recordings, electrophysiology spike trains, local field potentials, behavioral marker positions, single-trial behavioral events, etc. An **`experimentDesc.pdf`** file includes slides with a short description of the experiment (task design, recorded data types, numbers, etc.). A **`sessionInfo_<datasetID>.csv`** file within the dataset folder contains information about each experimental session (including session name, date, subject identity, etc.).

All data for each experimental session is saved in a separate folder named following the convention **`animal_ID_session_ID`** (e.g. `AstroDREADD30_20240919`). Within each session folder, there are three different types of files:

- **data** are stored in Matlab `.mat` or Numpy `.npz` files. Matlab and Numpy files are interchangeable and can be converted using the `mat_2_py` / `py_2_mat` functions. Each file contains data variables as time series (for continuous-time neural or behavioral data) or spike times (for spiking data) for each recorded unit over the whole session.
- Session-level metadata are stored in `.json` **schema** files and should be **duplicated** in **`sessionInfo.csv`** where possible. Schema files describe organization of data in associated array variables (dimension sizes, labels, index values, processing history). Session-level metadata are also duplicated as columns in **`sessionInfo.csv`**. Timestamps of each sampled time point relative to the session **`zero_time`** are stored in separate **`timestamps.mat` / `.npy`** files.
- **metadata** are stored in tabular **`.csv`** files: **`trialInfo_*.csv`** (trial-wise events) and **`<datatypeID>_metadata_*.csv`** (one row per unit, ROI, electrode, feature, etc.). Metadata files follow the naming conventions below.

Therefore, each **dataType** typically has four associated files within each experimental session folder: **`<datatypeID>_data`**.mat / `.npz`, **`<datatypeID>_schema`**.json, **`<datatypeID>_metadata`**.csv, and **`<datatypeID>_timestamps`**.mat / `.npz` (except where noted, e.g. spike times). **`<datatypeID>`** is the **full stream ID** (often camelCase with an optional informative prefix, e.g. `GCaMP7f_traces`, `pupil_behTSeries`, `spikeTimes`, `lfp`).

**Filename pattern (session folder).** Files inside **`animal_ID_session_ID/`** use **short names** only: **`<datatypeID>_data`**, **`<datatypeID>_schema`**, **`<datatypeID>_metadata`**, **`<datatypeID>_timestamps`** plus extension. **`datasetID`**, **`animal_ID`**, and **`session_ID`** are encoded in **parent folder names** (`<datasetID>/` and `<animal_ID>_<session_ID>/`), not repeated in each filename. Optional extra middle tokens may still appear for human readability; parsers should match on datatype ID, role, and extension.

**Dataset folder** still uses **`sessionInfo_<datasetID>.csv`**.

**Trial tables** inside the session folder: **`<datatypeID>.csv`** (e.g. `trialInfo.csv`, `passive_trialInfo.csv`) — no repeated dataset/session tokens in the filename.

![][image1]

*Schematics of dataset organization*

![][image2]

*Example dataset folder files organization*

![][image3]

*Example experimental session folder files organization*

**Important**: All data (e.g. timestamps, single-trial behavioral events) is expressed in a common time base — **seconds**, relative to the session **`zero_time`** (the standard reference is the start time of the physiology data collection, with data collected before the zero having a negative time, if any). The **`zero_time`** reference must be reported in **`sessionInfo.csv`**.

## **Experiment description**

This PDF file serves as a quick introduction to the experiment and the dataset. It includes summary information about the main dataset characteristics, its size, the experimental design and descriptions of dataset-specific metadata labels. This information should usually span 3–4 slides. The first slide should include 3–4 lines of dataset overview, a “unique characteristics” and a “caveats” section. The second slide should describe the experiment design. The third slide should summarize recordings (data types and Ns, e.g. number of subjects and ROIs for optical physiology). The fourth slide should provide a glossary of dataset-specific metadata labels.

## **Session info files**

These metadata files list each session as a row in a **`.csv`** file.

**File name:** `sessionInfo_<datasetID>.csv` (optional extra tokens allowed before `.csv` if the name still begins with `sessionInfo_`).

Rows correspond to sessions; columns are session properties. Names and formats align with DANDI/NWB-oriented usage. **Required** properties include:

| Column | Description |
| :---- | :---- |
| institution | Institution name, e.g. `MIT` |
| lab | Laboratory name, e.g. `SurLab` |
| experimenter | Full name of the experimenter who collected the data |
| animal_ID | Animal identifier |
| session_ID | Session identifier |
| session_date | Start date of the session (**`YYYY-MM-DD`**). No dunder in the column name. |
| species | Latin binomial, e.g. `Mus musculus` |
| sex | `M`, `F`, `O` (other), or `U` (unknown) |
| age__days | Age in **days** (numeric). |
| strain | Subspecies, breed, or common genetic modification, e.g. `C57BL/6`, or `Wild Type` if not applicable |
| zero_time | Global time reference: which **full datatype ID** defines session zero (e.g. `lfp`, `GCaMP7f_traces`, `spikeTimes`). Exactly **one** stream sets the clock; all other streams align to it. By default, use the **start of physiology acquisition**. |

**Optional** standardized properties include:

- Boolean columns (0/1) for each **individual stream** recorded in that session. Use the **full datatype ID as the column header** — not a single aggregate flag per base type. Examples: `GCaMP7f_traces`, `pupil_behTSeries`, `wheel_behTSeries` (not one shared `traces` or `behTSeries` column). Fixed-ID modalities without a lab prefix use the base ID only (`spikeTimes`, `lfp`, `trialInfo`, …).
- **`trialInfo`**: one boolean column; at most **one** trial table per session.
- `area` — recording area name(s); comma-separated if multiple areas were recorded simultaneously.
- `condition` — experimental condition labels (unique identifiers).
- `related_publication` — reference including DOI for related publication / preprocessing details.
- Hardware readouts such as **laser power**, **PMT**, or **Pockels** controls are often **arbitrary instrument units**. Prefer **numeric** columns for the readout and add a **separate optional calibration / conversion column** (or documented scale factor) when converting to physical units; supplying calibration is **recommended**.

To keep each session folder self-contained, include a single-session copy of the file as **`sessionInfo_single_session.csv`** (same schema; one row).

Session-level fields that were historically only in **schema JSON** (e.g. acquisition path, filter type) should appear in **`sessionInfo.csv`** when they apply to the whole session. Where a field would have used a unit in a **schema key**, prefer a **plain column name** in **`sessionInfo.csv`** and encode the quantity in **cell values** using the **`base__unit`** pattern (e.g. `amplitude__V`) when the cell holds a **unit tag**; use **numeric** columns with documented SI units in prose when the column is purely numeric.

![][image4]

## *Example sessionInfo csv file*

## **Neural and continuous-time behavioral data**

These files hold continuous-time physiology (fluorescence, LFP, …) or behavioral streams (pupil, marker positions, …). Each **dataType** has **data**, **schema** (optional if fully mirrored in `sessionInfo`), **metadata**, and **timestamps** (except where noted).

**data** and **schema** share one **`.mat`** or **`.npz`** file. **File name:** `<datatypeID>_data_<datasetID>_<animal_ID>_<session_ID>` (optional extra tokens allowed).

**metadata** is tabular: rows are recorded **units** or **ROIs** (or electrodes, events, features, …); columns use standardized **snake_case** names. **File name:** `<datatypeID>_metadata_<datasetID>_<animal_ID>_<session_ID>.csv`.

**timestamps** (when required): `<datatypeID>_timestamps_<datasetID>_<animal_ID>_<session_ID>`.mat / `.npz`.

**Currently covered data types:** Optical physiology (fluorescence traces); local field potentials; spike times; spike waveforms; behavioral events; behavioral time series.

**Standards for different data types**

| Data type | dataTypeID + (Mat / Python shape) | schema name | Index / unit label |
| :---- | :---- | :---- | :---- |
| **Optical physiology** (raw fluorescence traces) | Base ID **`traces`**; optional informative prefix → full **`<datatypeID>`** (e.g. `GCaMP7f_traces`). Same layout for all streams. Mat: `[time × ROIs]` doubles. Python: `(time, ROIs)` float ndarray. | `<datatypeID>_schema` (`.json`) | ROI |
| **Spike times** | `spikeTimes`. Matlab: `{1 × n_units}` cell of variable-length `[1 × n_spikes]` arrays. Python: `(1, n_units)` object ndarray of `(n_spikes,)` float arrays. | spikeTimesSchema — *no timestamps file* | unit |
| **Spike waveforms** | `spikeWaves`. Mat: `[waveform sample index × units]` doubles (first axis: **sampling time** along the waveform snippet, distinct from experiment clock time). Python: `(waveform_samples, units)` ndarray. Provide **`sample_frequency__Hz`** in schema or session info. | spikeWavesSchema | unit |
| **Local field potentials** | `lfp`. Mat: `[time × units]` doubles. Python: `(time, units)` ndarray. **First dimension is time** (aligned with `timestamps`). | lfpSchema | electrode |
| **Behavioral events** | `behEvents` (optional prefix, e.g. `lick_behEvents`). Mat: `{1 × n_events}` cell arrays. Python: `(1, n_events)` object ndarray. | behEventsSchema — *no timestamps file* | events |
| **Behavioral time series** | Base ID **`behTSeries`**; optional prefix → full **`<datatypeID>`** (e.g. `pupil_behTSeries`, `wheel_behTSeries`). Mat: `[time × features]`. Python: `(time, features)`. | `<datatypeID>_schema` | features |
| *Deprecated (use behEvents / behTSeries)* | lever, licking, pupil, movement | — | — |

**Table 1:** Standard variable names and array layouts. Use **units** or **ROIs**, not “neurons”, when describing the **unit** dimension.

**Schema fields** (`.json`): describe array layout for the associated **data** variable. **Shared keys** (when schema is used) — **snake_case** for tabular semantics:

| Key | Description |
| :---- | :---- |
| data_unit_measurement | String; unit tag for stored values. Prefer **`base__unit`** form (e.g. `amplitude__V`). Duplicated in **`sessionInfo.csv`** where applicable. |
| X_dim / Y_dim | Labels for dimensions (e.g. `time`, `channel`). |
| X_size / Y_size | Integer sizes (no `__count` suffix in the key name). |
| X_idx / Y_idx | Index values along each dimension. When the dimension is **time**, values are **seconds** relative to **`zero_time`**. Omitted for **spikeTimes** (times live in the spike arrays). |
| sample_frequency__Hz | Sampling frequency in Hz (float). |

**Data-type-specific** schema / metadata (and typical **`dataType_metadata.csv`** columns) — use **`um`** in names for micrometers:

| Data type | Specific schema / session fields | metadata (per unit / ROI / channel) |
| :---- | :---- | :---- |
| **Optical physiology** | Laser name, objectives, `pixel_size` (µm in value; optional column `pixel_size_calibration`), FOV sizes in pixels, FOV depth (**`um`**), indicator, **`wavelength__nm`**, PMT / laser power columns with optional **calibration** columns as above, `detection_software` | `roi_ID`, `roi_x_coordinate`, `roi_y_coordinate`, `area`, **`depth__um`**, `roi_center_x`, `roi_center_y` |
| **Spike times** | `probe`, `acquisition_software`, `sorting_software`, **`filter_type`**, **`filter_cutoff_low__Hz`**, **`filter_cutoff_high__Hz`**, `quality_metric` | `unit_ID`, **`depth__um`**, `area`, `spike_sorting_ID`, `quality`, `grid_location` (row, col) |
| **Spike waveforms** | `probe`, `clustering_algorithm` | `unit_ID`, `primary_channel` (see LFP `channel_ID`) |
| **Local field potentials** | `probe`, **`filter_type`**, **`filter_cutoff_low__Hz`**, **`filter_cutoff_high__Hz`** | `channel_ID`, `channel_label`, `area`, `grid_location` |
| **Behavioral time series** | — | `feature_ID`, `feature_label` |
| **Behavioral events** | — | `event_ID`, `event_label` |

**Table 2:** Schema, session, and per-unit metadata (representative fields).

## **Trial information files**

**One table per session.** Set **`trialInfo = 1`** in **`sessionInfo.csv`** when present. **File name:** `trialInfo_<datasetID>_<animal_ID>_<session_ID>.csv` (optional extra middle tokens allowed).

Tabular **`.csv`**: one row per trial. **Required** columns (headers use **dunder + unit** where applicable):

| Column | Description |
| :---- | :---- |
| start_time__s | Trial start (seconds relative to **`zero_time`**) |
| stop_time__s | Trial end (seconds relative to **`zero_time`**) |

**Stimuli**

| Column | Description |
| :---- | :---- |
| stimulus_onset__s | Stimulus onset (s) |
| stimulus_offset__s | Stimulus offset (s) |
| tone_frequency__Hz | Auditory tone frequency |
| tone_intensity__dB | Auditory level (dB) |
| grating_orientation__degrees | Grating orientation |
| grating_spatial_frequency__cycles_per_degree | Visual grating spatial frequency (cycles per degree); if your pipeline uses a different convention, document it in the dataset README |
| grating_drift_speed__m_per_s | Drift speed (m/s) |
| grating_drift_direction__degrees | Drift direction |

**Behavioral outputs**

| Column | Description |
| :---- | :---- |
| reaction_time__s | Reaction time (s) from `stimulus_onset__s` |
| output | Categorical labels (`press`, `no_press`, …) |
| num_licks | Count of licks in the trial (integer) |

**Reinforcement**

| Column | Description |
| :---- | :---- |
| reward | Boolean: reward delivered |
| punish | Boolean: punishment delivered |

**Outcome**

| Column | Description |
| :---- | :---- |
| correct | **Binary** `0` or `1` (`1` = correct). Non-binary legacy encodings should be converted with a validation warning. |

![][image5]

*Example trialInfo file*

If there are multiple events of the same type, append an integer to the label (e.g. `stimulus_onset__s_1`, `stimulus_onset__s_2`) — keep the same **`__s`** / unit pattern before the suffix.

## **FAQ**

**Where should I store behavioral data?**

Three structures: **`trialInfo.csv`** (trial-wise), **`behEvents`** (event times without strict trials), **`behTSeries`** (continuous streams). **`behEvents`** follows spike-time–like storage; **`behTSeries`** follows traces-like storage (**time × features**, time on the first axis).

## **Functions**

- **trials_parse**: data, schema, metadata, and `trialInfo` → trial-aligned arrays (**time × units × trials**), aligned to a chosen `trialInfo` field.
- **validate**: validate a file given its type (data, schema, `trialInfo`, …).
- **surlab_2_nwb**: build per-session NWB files compatible with DANDI.

Useful link for NWB metadata keywords (e.g. NWB 2.9): https://nwb-schema.readthedocs.io/en/latest/format.html

**mat_2_py** / **py_2_mat**: convert Matlab ↔ Python file containers.

Converters from common lab tools (e.g. Suite2P) into SurLab layout may be provided separately.
