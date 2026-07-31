"""
Configuration loader.

All secrets come from environment variables (loaded from a local .env file
via python-dotenv). Never commit your real .env — .gitignore already covers it.
"""
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            f"Copy .env.example to .env and fill it in."
        )
    return value


@dataclass(frozen=True)
class Settings:
    # LeetCode auth (grab these from your browser's cookies while logged in)
    leetcode_session: str
    leetcode_csrf_token: str
    leetcode_username: str

    # GitHub target
    github_token: str
    github_repo: str  # "username/repo-name"
    github_branch: str

    # Behavior
    poll_interval_seconds: int
    submission_fetch_limit: int
    commit_author_name: str
    commit_author_email: str


def _github_repo() -> str:
    # GITHUB_REPO wins if set explicitly. Otherwise fall back to the
    # GITHUB_REPOSITORY var Actions injects automatically ("owner/repo"), so
    # no repo-specific config is needed when running as a workflow.
    return os.getenv("GITHUB_REPO") or _require("GITHUB_REPOSITORY")


def _github_token() -> str:
    # In Actions, prefer the run's own token (passed in as GITHUB_TOKEN from
    # secrets.GITHUB_TOKEN) over a manually-configured PAT.
    return os.getenv("GITHUB_TOKEN") or _require("GH_PAT")


def load_settings() -> Settings:
    return Settings(
        leetcode_session=_require("LEETCODE_SESSION"),
        leetcode_csrf_token=_require("LEETCODE_CSRF_TOKEN"),
        leetcode_username=_require("LEETCODE_USERNAME"),
        github_token=_github_token(),
        github_repo=_github_repo(),
        github_branch=os.getenv("GITHUB_BRANCH", "main"),
        poll_interval_seconds=int(os.getenv("POLL_INTERVAL_SECONDS", "30")),
        submission_fetch_limit=int(os.getenv("SUBMISSION_FETCH_LIMIT", "20")),
        commit_author_name=os.getenv("COMMIT_AUTHOR_NAME", "leetcode-sync-bot"),
        commit_author_email=os.getenv("COMMIT_AUTHOR_EMAIL", "bot@example.com"),
    )
