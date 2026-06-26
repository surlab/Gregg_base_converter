"""End-to-end entry point for the converter.

Run from repo root: python -m src.main
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import config as cfg


def main():
  """Orchestrate load → convert → validate → save."""
  raise NotImplementedError(
      "Implement the converter in src/ modules, then wire steps here. "
      "See example_past_converter/ and agent_materials/agent_handoff_instructions.md."
  )


if __name__ == "__main__":
    main()
