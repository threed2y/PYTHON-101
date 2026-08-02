"""
Diagnostic: checks whether LEETCODE_USERNAME resolves to a real profile and
shows total solved counts — independent of recentAcSubmissionList. Useful
for telling apart "wrong username" from "privacy setting hides recent
submissions". Run via the maintenance.yml workflow.
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


client = LeetCodeClient(
    _require("LEETCODE_SESSION"),
    _require("LEETCODE_CSRF_TOKEN"),
    _require("LEETCODE_USERNAME"),
)
profile = client.get_user_profile()
if not profile:
    print(json.dumps({"matchedUser": None, "note": "Username did not resolve — check LEETCODE_USERNAME"}, indent=2))
else:
    print(json.dumps(profile, indent=2))
