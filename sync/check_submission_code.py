"""
Diagnostic #3: dumps the raw submissionDetails response for one specific
submission ID, so we can see exactly what LeetCode returns (or doesn't) for
that submission -- useful when the code field comes back empty for certain
problem types.

Usage:
    python tools/check_submission_code.py <submission_id>

Get the submission_id from tools/check_recent.py's output (the "id" field
for the submission you care about).
"""
import json
import os
import sys
from pathlib import Path

SYNC_DIR = Path(__file__).parent.parent / "sync"
sys.path.insert(0, str(SYNC_DIR))

from dotenv import load_dotenv
load_dotenv(SYNC_DIR / ".env")

from leetcode_client import LeetCodeClient  # noqa: E402


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        sys.exit(f"Missing {name}.")
    return value


if len(sys.argv) != 2:
    sys.exit("Usage: python check_submission_code.py <submission_id>")

client = LeetCodeClient(
    _require("LEETCODE_SESSION"),
    _require("LEETCODE_CSRF_TOKEN"),
    _require("LEETCODE_USERNAME"),
)
details = client.get_submission_details(sys.argv[1])
print(json.dumps(details, indent=2))