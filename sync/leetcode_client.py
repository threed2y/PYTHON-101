"""
Thin client around LeetCode's (undocumented) GraphQL API.

Uses your logged-in session cookie so it can pull full submission source code,
which the public recentAcSubmissionList endpoint alone does not expose.
"""
import logging
import time
from typing import Any, Optional

import requests

logger = logging.getLogger("leetcode_sync.leetcode_client")

GRAPHQL_URL = "https://leetcode.com/graphql"

RECENT_AC_QUERY = """
query recentAcSubmissions($username: String!, $limit: Int!) {
  recentAcSubmissionList(username: $username, limit: $limit) {
    id
    title
    titleSlug
    timestamp
    lang
  }
}
"""

SUBMISSION_DETAILS_QUERY = """
query submissionDetails($submissionId: Int!) {
  submissionDetails(submissionId: $submissionId) {
    runtimeDisplay
    memoryDisplay
    code
    lang {
      name
      verboseName
    }
  }
}
"""

QUESTION_DATA_QUERY = """
query questionData($titleSlug: String!) {
  question(titleSlug: $titleSlug) {
    questionId
    questionFrontendId
    title
    difficulty
    topicTags {
      name
    }
  }
}
"""

# LeetCode lang name -> file extension
LANG_EXTENSIONS = {
    "python": "py",
    "python3": "py",
    "c": "c",
    "cpp": "cpp",
    "csharp": "cs",
    "java": "java",
    "javascript": "js",
    "typescript": "ts",
    "php": "php",
    "swift": "swift",
    "kotlin": "kt",
    "dart": "dart",
    "golang": "go",
    "ruby": "rb",
    "scala": "scala",
    "rust": "rs",
    "racket": "rkt",
    "erlang": "erl",
    "elixir": "ex",
    "mysql": "sql",
    "mssql": "sql",
    "oraclesql": "sql",
    "pythondata": "py",
    "postgresql": "sql",
    "bash": "sh",
}


class LeetCodeClient:
    def __init__(self, session_cookie: str, csrf_token: str, username: str):
        self.username = username
        self.session = requests.Session()
        self.session.cookies.set("LEETCODE_SESSION", session_cookie, domain="leetcode.com")
        self.session.cookies.set("csrftoken", csrf_token, domain="leetcode.com")
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "Referer": "https://leetcode.com",
                "x-csrftoken": csrf_token,
                "User-Agent": "leetcode-github-sync/1.0",
            }
        )

    def _post(self, query: str, variables: dict[str, Any], retries: int = 3) -> dict[str, Any]:
        last_exc: Optional[Exception] = None
        for attempt in range(1, retries + 1):
            try:
                resp = self.session.post(
                    GRAPHQL_URL, json={"query": query, "variables": variables}, timeout=15
                )
                resp.raise_for_status()
                payload = resp.json()
                if "errors" in payload and payload["errors"]:
                    raise RuntimeError(f"GraphQL errors: {payload['errors']}")
                return payload["data"]
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                wait = 2 ** attempt
                logger.warning("LeetCode API call failed (attempt %d/%d): %s. Retrying in %ds",
                                attempt, retries, exc, wait)
                time.sleep(wait)
        raise RuntimeError(f"LeetCode API call failed after {retries} attempts") from last_exc

    def get_recent_ac_submissions(self, limit: int) -> list[dict[str, Any]]:
        data = self._post(RECENT_AC_QUERY, {"username": self.username, "limit": limit})
        return data.get("recentAcSubmissionList", []) or []

    def get_submission_details(self, submission_id: int) -> dict[str, Any]:
        data = self._post(SUBMISSION_DETAILS_QUERY, {"submissionId": int(submission_id)})
        return data.get("submissionDetails", {}) or {}

    def get_submission_details_with_code(self, submission_id: int, max_attempts: int = 4,
                                          base_delay: float = 3.0) -> dict[str, Any]:
        """Like get_submission_details, but retries with backoff if `code`
        comes back empty. LeetCode's write path (especially for database/SQL
        submissions) can lag behind recentAcSubmissionList by a few seconds,
        so an immediate query sometimes returns every field except code.
        Returns whatever the last attempt got, even if still empty — the
        caller decides what to do with that.
        """
        details: dict[str, Any] = {}
        for attempt in range(1, max_attempts + 1):
            details = self.get_submission_details(submission_id)
            if details.get("code"):
                return details
            if attempt < max_attempts:
                delay = base_delay * attempt
                logger.warning(
                    "submissionDetails for %s returned no code (attempt %d/%d). "
                    "Retrying in %.0fs — this is usually just replication lag.",
                    submission_id, attempt, max_attempts, delay,
                )
                time.sleep(delay)
        return details

    def get_question_data(self, title_slug: str) -> dict[str, Any]:
        data = self._post(QUESTION_DATA_QUERY, {"titleSlug": title_slug})
        return data.get("question", {}) or {}

    @staticmethod
    def extension_for_lang(lang_slug: str) -> str:
        return LANG_EXTENSIONS.get(lang_slug.lower(), "txt")