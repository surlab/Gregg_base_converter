# Agent handoff — building a new SurLab converter

## Goal

Implement a converter that reads the user's raw session data and writes **SurLab layout**. When finished, it must run **end-to-end** from `python -m src.main` (and `src/tests.py`).  

`example_past_converter/` is **reference only** — do not make it runnable; use it for module patterns and mapping-table examples.

## Read first

1. `agent_materials/SurLab data format documentation.md`
2. `sur_nwb_conversion_table.csv` — authoritative SurLab → NWB field spec (do not rewrite)
3. `example_past_converter/` — architecture sentinel (especially `src/` modules and `custom_to_sur_mapping_table.csv`)

## You author

| Artifact | Location |
|----------|----------|
| `custom_to_sur_mapping_table.csv` | Repo root — map **this** source format → SurLab artifacts/fields |
| `config.py` | Fill `dataset_id`, IDs, paths under `EXAMPLE_*` dirs |
| `src/*.py` | Discovery, clock alignment, I/O, validation, orchestration |
| `src/main.py` | Wire load → convert → validate → save |
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
- Viewing `sur_nwb_conversion_table.csv` and `custom_to_sur_mapping_table.csv`
- Inspecting example SurLab `*_schema.json` and `*_metadata.csv` in `example_past_converter/`

**You must add** cells that visualize **pre-conversion** structure once user data exists, e.g.:

- List/glob files under `EXAMPLE_SESSION_DIR_GOES_HERE/example_session/`
- Peek at representative raw files (CSV headers, XML timing, array shapes)

## Validation

Validate exports against required fields in `sur_nwb_conversion_table.csv` (see `example_past_converter/src/validate_surlab.py` for patterns).

## Optional dependencies

List any extras in `README.md` — do not bloat `environment_cross_platform.yml` unless the whole lab needs them.

## Clarify before coding

Raise questions on ambiguous mappings, missing mandatory SurLab fields, or clock policy. Propose an implementation plan and wait for approval before large changes.
