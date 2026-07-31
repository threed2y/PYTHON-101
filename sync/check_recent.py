"""
Diagnostic: dumps the raw recentAcSubmissionList response so you can check
whether a specific submission (e.g. a database/SQL problem) is actually
present in what LeetCode's API returns, before assuming the sync tool itself
is broken.

Local:    fill in sync/.env, then run `python tools/check_recent.py` from repo root
Actions:  trigger via the "Debug - Recent Submissions" workflow (workflow_dispatch)
"""
import json
import os
import sys
from pathlib import Path

# This script lives in tools/, but leetcode_client.py lives in sync/ — add
# that to sys.path so the import works regardless of where this is run from.
SYNC_DIR = Path(__file__).parent.parent / "sync"
sys.path.insert(0, str(SYNC_DIR))

from dotenv import load_dotenv
load_dotenv(SYNC_DIR / ".env")  # no-op if the file doesn't exist (e.g. in Actions)

from leetcode_client import LeetCodeClient


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        sys.exit(f"Missing {name}. Set it in sync/.env locally, or as a repo secret in Actions.")
    return value


client = LeetCodeClient(
    _require("LEETCODE_SESSION"),
    _require("LEETCODE_CSRF_TOKEN"),
    _require("LEETCODE_USERNAME"),
)
subs = client.get_recent_ac_submissions(limit=20)
print(json.dumps(subs, indent=2))