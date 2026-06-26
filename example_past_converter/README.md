# Tricolor → SurLab reference (non-runnable)

This folder preserves the **architecture and materials** from a completed Tricolor 2P converter. It is **not** intended to run end-to-end — no demo data binaries are included.

Use it when implementing a new converter:

- **`src/`** — module layout (`discover_session`, `clock_alignment`, `surlab_io`, `validate_surlab`, etc.)
- **`custom_to_sur_mapping_table.csv`** — example source → SurLab mapping
- **`config.py`** — filled paths and IDs for the Tricolor case
- **`EXAMPLE_*`** — directory naming convention with small SurLab sentinels
- **`agent_materials/`** — archived build notes from the original session

Copy patterns into the **repo root** `src/` when building a new converter. The new converter must run E2E; this example does not.
