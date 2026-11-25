"""Check data/ for missing fields, duplicates, bad IDs and unparsable leaderboard numbers.

Run: python scripts/validate.py   (CI runs it on every pull request)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import validate  # noqa: E402

if __name__ == "__main__":
    errors = validate()
    if errors:
        print("data/ has problems:\n  " + "\n  ".join(errors))
        sys.exit(1)
    print("data/ is valid")
