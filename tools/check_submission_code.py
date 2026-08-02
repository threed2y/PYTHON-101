"""
Diagnostic: dumps the raw submissionDetails response for one submission ID
(using the same retry-on-empty-code logic main.py uses), so you can see
exactly what LeetCode returns for a specific submission. Run via the
maintenance.yml workflow, passing the ID as a workflow input.

Usage:
    python tools/check_submission_code.py <submission_id>
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "sync"))
from leetcode_client import LeetCodeClient  # noqa: E402


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        sys.exit(f"Missing {name}.")
    return value


if len(sys.argv) != 2 or not sys.argv[1].strip():
    sys.exit("Usage: python check_submission_code.py <submission_id>")

client = LeetCodeClient(
    _require("LEETCODE_SESSION"),
    _require("LEETCODE_CSRF_TOKEN"),
    _require("LEETCODE_USERNAME"),
)
details = client.get_submission_details_with_code(sys.argv[1].strip(), max_attempts=5, base_delay=3.0)
print(json.dumps(details, indent=2))
