"""Run the complete Legacy AI Gateway test suite."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

suite = unittest.defaultTestLoader.discover(
    start_dir=str(ROOT / "tests"),
    pattern="test_*.py",
    top_level_dir=str(ROOT),
)
result = unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
