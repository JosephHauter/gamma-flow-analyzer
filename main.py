"""Run the package under src/ so both `python main.py` and `python -m titan_guardian` work.

This shim simply ensures older workflows keep working after the repo was reorganized.
"""

import sys
from pathlib import Path

# Add src/ to sys.path so the package can be imported when running this file directly.
ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

if __name__ == "__main__":
    # Run the package as a module
    import runpy
    runpy.run_module('titan_guardian', run_name='__main__')