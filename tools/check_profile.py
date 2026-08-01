"""
Diagnostic #2: checks whether LEETCODE_USERNAME resolves to a real profile
and shows total solved counts via matchedUser/submitStatsGlobal — a query
path that's independent of recentAcSubmissionList. Useful for telling apart
"wrong username" from "privacy setting hides recent submissions".
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

QUERY = """
query userProfile($username: String!) {
  matchedUser(username: $username) {
    username
    profile {
      realName
    }
    submitStats: submitStatsGlobal {
      acSubmissionNum {
        difficulty
        count
      }
    }
  }
}
"""


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
data = client._post(QUERY, {"username": client.username})
print(json.dumps(data, indent=2))