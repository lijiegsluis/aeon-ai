import os
import sys
import tempfile
from pathlib import Path

# Isolated database per test run, set before any backend module is imported.
_TMP = tempfile.mkdtemp(prefix="aeon-intel-test-")
os.environ["AEON_INTEL_DB_PATH"] = str(Path(_TMP) / "intelligence.db")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
