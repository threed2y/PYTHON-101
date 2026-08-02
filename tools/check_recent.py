"""
Diagnostic: dumps the raw recentAcSubmissionList response so you can check
whether a specific submission is actually present in what LeetCode's API
returns. Run via the maintenance.yml workflow.
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
        sys.exit(f"Missing {name}. This must be passed as a repo secret via the workflow's env: block.")
    return value


client = LeetCodeClient(
    _require("LEETCODE_SESSION"),
    _require("LEETCODE_CSRF_TOKEN"),
    _require("LEETCODE_USERNAME"),
)
subs = client.get_recent_ac_submissions(limit=int(os.getenv("SUBMISSION_FETCH_LIMIT", "20")))
print(json.dumps(subs, indent=2))
