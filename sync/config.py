"""
Configuration loader — GitHub Actions only.

Every value arrives as an environment variable set by the workflow: repo
secrets for LeetCode credentials, and GitHub's own injected context
(GITHUB_TOKEN, GITHUB_REPOSITORY) for the target repo. There is no local
.env / Docker / systemd path — this project runs exclusively inside
GitHub Actions, targeting the repo it runs inside.
"""
import os
from dataclasses import dataclass


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            f"Set it as a repo secret (Settings -> Secrets and variables -> Actions) "
            f"and pass it into the workflow step's `env:` block."
        )
    return value


@dataclass(frozen=True)
class Settings:
    leetcode_session: str
    leetcode_csrf_token: str
    leetcode_username: str
    github_token: str
    github_repo: str
    github_branch: str
    submission_fetch_limit: int
    commit_delay_seconds: float
    pending_escalate_threshold: int


def load_settings() -> Settings:
    return Settings(
        leetcode_session=_require("LEETCODE_SESSION"),
        leetcode_csrf_token=_require("LEETCODE_CSRF_TOKEN"),
        leetcode_username=_require("LEETCODE_USERNAME"),
        github_token=_require("GITHUB_TOKEN"),
        # GITHUB_REPOSITORY is auto-injected by Actions ("owner/repo") — no
        # manual config needed for the common case of syncing into the repo
        # this workflow lives in.
        github_repo=os.getenv("GITHUB_REPO") or _require("GITHUB_REPOSITORY"),
        github_branch=os.getenv("GITHUB_BRANCH", "main"),
        submission_fetch_limit=int(os.getenv("SUBMISSION_FETCH_LIMIT", "20")),
        commit_delay_seconds=float(os.getenv("COMMIT_DELAY_SECONDS", "1.0")),
        pending_escalate_threshold=int(os.getenv("PENDING_ESCALATE_THRESHOLD", "5")),
    )
