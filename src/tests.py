"""End-to-end tests for the converter.

The agent adds tests here once the new converter runs end-to-end.
See agent_materials/agent_handoff_instructions.md.
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def test_placeholder():
    """Remove this stub when real tests are added."""
    assert True
