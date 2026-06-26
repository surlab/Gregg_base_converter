# Agent handoff — building a new SurLab converter

## Goal

Implement a converter that reads the user's raw session data and writes **SurLab layout**. When finished, it must run **end-to-end** from `python -m src.main` (and `src/tests.py`).  

`example_past_converter/` is **reference only** — do not make it runnable; use it for module patterns and mapping-table examples.

## Read first

Copy the prompt in **`agent_materials/COPY_AND_PASTE_TO_AGENT.txt`** into your agent session, then read:

1. `agent_materials/SurLab data format documentation.md`
2. `agent_materials/sur_nwb_conversion_table.csv` — authoritative SurLab → NWB field spec (do not rewrite)
3. `example_past_converter/` — architecture sentinel (especially `src/` modules and `custom_to_sur_mapping_table.csv`)

## You author

| Artifact | Location |
|----------|----------|
| `custom_to_sur_mapping_table.csv` | Repo root — map **this** source format → SurLab artifacts/fields |
| `metadata_defaults.csv` | Repo root — user/agent dataset & session metadata (strain, species, …); **never hardcode in `.py`** |
| `config.py` | Fill `dataset_id`, IDs, paths under `EXAMPLE_*` dirs |
| `src/*.py` | Discovery, clock alignment, I/O, validation, orchestration |
| `src/metadata_gap_audit.py` | Parse spec table; build gap report for user (required + recommended) |
| `src/main.py` | Wire load → convert → validate → save; run gap audit before/after |
| `src/tests.py` | End-to-end test on user data in `EXAMPLE_SESSION_DIR_GOES_HERE/` |
| `src/explore_data.ipynb` | **Pre-conversion** visualization cells for this source (see below) |

## Directory placeholders (keep exact names)

```
EXAMPLE_SESSION_DIR_GOES_HERE/example_session/     ← raw inputs
EXAMPLE_SURFORMAT_DATASET_WILL_APPEAR_HERE/      ← SurLab export
EXAMPLE_ACCESS_CODE_GOES_HERE/                   ← reference pipeline code
```

## Clock and arrays

- Align all streams to the session `zero_time` documented in SurLab spec.
- Canonical array layout: axis 0 = time, axis 1 = ROIs/features.
- Prefer native sample rates unless the user specifies otherwise.

## Notebook (`src/explore_data.ipynb`)

Template cells already cover:

- Entry points (`config.py`, `python -m src.main`)
- Viewing `agent_materials/sur_nwb_conversion_table.csv` and `custom_to_sur_mapping_table.csv`
- Inspecting example SurLab `*_schema.json` and `*_metadata.csv` in `example_past_converter/`

**You must add** cells that visualize **pre-conversion** structure once user data exists, e.g.:

- List/glob files under `EXAMPLE_SESSION_DIR_GOES_HERE/example_session/`
- Peek at representative raw files (CSV headers, XML timing, array shapes)

## Metadata gap audit (required step)

**Do not skip this.** Run it **before coding** (during the implementation plan) and **again after every conversion run**.

### Purpose

Identify metadata that the SurLab spec marks as **required** or **recommended** but that is **not available** from raw data, access code, or sidecars. **Advertise every gap loudly** — do not silently invent values or hide omissions.

The converter **must write whatever it can** (partial export is OK). It must **not** fail silently on missing metadata. Missing fields are **not** a reason to skip writing arrays/files that are ready.

### User-provided metadata (`metadata_defaults.csv`)

Values that are **identical across sessions** (e.g. `strain`, `species`, `institution`, `lab`, `experimenter`) or **session-specific overrides** (e.g. `sex`, `age__days`) belong in **`metadata_defaults.csv`** at the repo root — **not** hardcoded in Python.

| Column | Meaning |
|--------|---------|
| `fieldname` | SurLab / sessionInfo column name |
| `value` | User- or agent-supplied value (leave empty if unknown) |
| `scope` | `dataset` (all sessions) or `session` (per-animal overrides) |
| `artifact` | Usually `sessionInfo`; stream fields use `schema` / `metadata` |
| `datatypeID` | Stream ID when scope is stream-specific; else empty |
| `provenance` | e.g. `user supplied`, `agent inferred` |
| `notes` | Free text |

**Workflow:** During the gap audit, ask the user for missing dataset-level fields. **Save their answers into `metadata_defaults.csv`** (and commit the file). The converter reads this CSV at runtime. If the user provides values only in chat, the agent must persist them to the CSV before considering the task complete.

### How to build the checklist

Use **`agent_materials/sur_nwb_conversion_table.csv`**. For each `metadata_field` row:

| Scope | Which rows to include |
|-------|----------------------|
| **Session / base** | `requirement_condition` = `always` (stage 1 `sessionInfo_*`) |
| **Stream-specific** | `if_datatype_present:<datatypeID>` **only for streams you export** |

Merge in values from `metadata_defaults.csv` (dataset scope first, then session overrides) before marking a field filled.

### What counts as “missing”

**Missing** — no value after checking raw data, access code, `metadata_defaults.csv`, and other sidecars.  
**Filled** — value available with stated provenance.  
**Inferred** — value guessed; list under “please confirm” until user approves (then move to `metadata_defaults.csv` or document acceptance in the report).

### Be loud: where to advertise gaps

On **every** gap audit and conversion run, output missing metadata in **all** of these places:

1. **Console / log** — `logging.warning` for each missing **required** field; `logging.info` or `warning` for **recommended**. Print a short **summary block** at end of run (see below).
2. **`logs/metadata_gap_report.md`** — full report (`config.metadata_gap_report_log_path`).
3. **Dataset directory** — `{output_dataset_root}/metadata_gap_report.md` (same content as logs copy, so users see it next to `sessionInfo_*.csv`).

During the **implementation plan** (before coding), also paste the summary into the **agent chat** so the user sees it in the prompt.

### Summary format (console + chat)

Use a highly visible banner. For **recommended** gaps, **list up to 3 example field names**, then abbreviate:

```
================================================================================
METADATA GAP REPORT — <dataset_id> / <animal_id> / <session_id>
================================================================================
MISSING REQUIRED — session (sessionInfo): sex, age__days
MISSING REQUIRED — GCaMP8m_traces (schema): indicator
MISSING RECOMMENDED — GCaMP8m_traces (schema): sample_frequency__Hz, acquisition_software, detection_software — and 2 more (see metadata_gap_report.md)
MISSING RECOMMENDED — pupil_behTSeries (metadata): 5 fields missing (see metadata_gap_report.md)
================================================================================
Wrote partial SurLab export. Resolve required gaps or update metadata_defaults.csv.
================================================================================
```

Full field lists live only in the markdown reports (logs + dataset dir).

### Metadata Gap Report (markdown files)

Write identical content to **both** `logs/metadata_gap_report.md` and `{output_dataset_root}/metadata_gap_report.md`:

```markdown
# Metadata gap report — <dataset_id> / <animal_id> / <session_id>
Generated: <ISO timestamp>

## Streams exported
- GCaMP8m_traces
- …

## Missing required
| Field | Level | Artifact | Stream | Notes |
|-------|-------|----------|--------|-------|
| sex | session | sessionInfo | — | not in raw; not in metadata_defaults.csv |

## Missing recommended (full list)
### sessionInfo (session)
- area
- condition

### GCaMP8m_traces — schema
- sample_frequency__Hz
- …

## Filled / inferred (user please confirm)
| Field | Value | Provenance |
|-------|-------|------------|
| strain | flex-GCaMP8m x CamkII-Cre | metadata_defaults.csv |

## User actions
- Add rows to metadata_defaults.csv for dataset-wide fields
- …
```

### Rules

1. **Write what you can** — export streams even when required metadata is missing; leave columns empty or omit keys only where the spec allows.
2. **Required gaps** — be **very loud**; do not declare the converter complete until the user supplies values (via `metadata_defaults.csv` or chat → CSV), confirms inference, or explicitly accepts omission (record in report).
3. **Recommended gaps** — always summarize in console/chat; full list in markdown only.
4. **No hardcoding** — dataset-wide strain/species/institution/etc. go in `metadata_defaults.csv`, not `config.py` or module constants.
5. **Per-stream scope** — only audit schema/metadata rows for streams actually exported.
6. **Re-run after every conversion** — compare written `sessionInfo_*.csv`, `*_schema.json`, `*_metadata.csv` to the checklist.

### Implementation

Add **`src/metadata_gap_audit.py`** that:

- Parses `sur_nwb_conversion_table.csv`
- Loads `metadata_defaults.csv`
- Accepts exported datatype list + dict of observed values/provenance
- Returns structured gaps; formats console summary (with “N more” for recommended); writes both markdown paths
- Called from `src/main.py` **after** export (and optionally before, during planning)

Wire a summary cell into `explore_data.ipynb` if helpful.

## Validation

Validate exports against required fields in `agent_materials/sur_nwb_conversion_table.csv` (see `example_past_converter/src/validate_surlab.py` for patterns).

## Optional dependencies

List any extras in `README.md` — do not bloat `environment_cross_platform.yml` unless the whole lab needs them.

## Clarify before coding

Raise questions on ambiguous mappings, missing mandatory SurLab fields, or clock policy. **Run the metadata gap audit and share the report with the user** as part of the implementation plan. Wait for approval before large changes.
