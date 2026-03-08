"""Root conftest.py — adds the repo root and cli/ to sys.path so pytest can find `engine` and `display`."""

import sys
from pathlib import Path

# Ensure the repo root and cli/ are on the path for all test modules
_root = Path(__file__).resolve().parent
sys.path.insert(0, str(_root))
sys.path.insert(0, str(_root / "cli"))
