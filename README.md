# Gregg_base_converter — SurLab converter template

Template repository for building **source format → SurLab** converters at the Sur lab (MIT).

## What this repo contains

| Path | Purpose |
|------|---------|
| `EXAMPLE_SESSION_DIR_GOES_HERE/` | User places raw session files here (`example_session/` subfolder) |
| `EXAMPLE_SURFORMAT_DATASET_WILL_APPEAR_HERE/` | Converter writes SurLab dataset output here |
| `EXAMPLE_ACCESS_CODE_GOES_HERE/` | Reference pipeline code from the source lab (`.py` / `.m`) |
| `agent_materials/sur_nwb_conversion_table.csv` | SurLab field spec (SurLab → NWB); read-only for converters |
| `custom_to_sur_mapping_table.csv` | **You author** — maps your source format → SurLab |
| `metadata_defaults.csv` | User/agent-edited provenance values (strain, species, etc.) — **not** hardcoded in Python |
| `config.py` | Paths and IDs — fill when implementing |
| `src/` | Converter modules + `main.py` entry point |
| `agent_materials/` | Spec docs, `COPY_AND_PASTE_TO_AGENT.txt`, and handoff instructions |
| `example_past_converter/` | **Non-runnable** reference (Tricolor architecture + code patterns) |

## Creating a new converter repo from this template

1. Use GitHub **“Use this template”** to create a new repository.
2. Clone to a Windows machine with conda on PATH.
3. Double-click **`dev_install_win.bat`** once. It will:
   - Ask for the new repo / environment name (replaces `replace_with_env_name` in text files)
   - Create the conda environment
   - Replace this README with `PROJECT_README.md` (converter-focused)
   - Remove one-time setup scripts (`dev_install_win.bat`, etc.)
4. After setup, end users install with **`user_install_win.bat`** only.

## For agents implementing a converter

Read **`agent_materials/agent_handoff_instructions.md`** before coding.

The **new** converter must run **end-to-end** when complete (`python -m src.main`, `main.bat`).  
`example_past_converter/` is reference material only — it does not need to run.

## Explore the format

Open **`src/explore_data.ipynb`** (or double-click `notebook_win_start.bat`) to view conversion tables and example SurLab schema/metadata files.

## Credit

Template by Gregg Heller (Sur lab, MIT).
