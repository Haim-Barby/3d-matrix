"""Put the repo root and src on sys.path so pytest can import the project."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for directory in (ROOT, ROOT / "src"):
    entry = str(directory)
    if entry not in sys.path:
        sys.path.insert(0, entry)
