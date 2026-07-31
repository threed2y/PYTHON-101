"""
Entry point: polls LeetCode for newly-accepted submissions and syncs each one
to GitHub as soon as it's detected, then keeps the stats README current.

Run:
    python main.py            # loop forever at the configured interval
    python main.py --once      # single pass, useful for cron/GitHub Actions
"""
import argparse
import logging
import sys
import time
from pathlib import Path

from config import load_settings
from github_sync import GitHubSync
from leetcode_client import LeetCodeClient
from state import SyncState

# Log dir is relative to this file, not the caller's cwd, so it behaves the
# same whether you run `python main.py` here or `python sync/main.py` from a
# repo root (as the GitHub Actions workflow does).
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler(LOG_DIR / "sync.log")],
)
logger = logging.getLogger("leetcode_sync.main")


def run_once(lc: LeetCodeClient, gh: GitHubSync, state: SyncState, fetch_limit: int) -> int:
    """Checks for new accepted submissions and syncs them. Returns count synced."""
    submissions = lc.get_recent_ac_submissions(limit=fetch_limit)
    new_subs = [s for s in submissions if not state.is_synced(s["id"])]

    if not new_subs:
        logger.info("No new submissions.")
        return 0

    # Oldest first, so commit history reads chronologically.
    new_subs.sort(key=lambda s: int(s["timestamp"]))

    synced_count = 0
    for sub in new_subs:
        try:
            details = lc.get_submission_details(sub["id"])
            question = lc.get_question_data(sub["titleSlug"])
            ext = lc.extension_for_lang(sub["lang"])

            gh.sync_solution(sub, details, question, ext)

            state.mark_synced(
                sub["id"],
                {
                    "problem_id": question.get("questionFrontendId", "0"),
                    "title": sub["title"],
                    "slug": sub["titleSlug"],
                    "difficulty": question.get("difficulty", "Unknown"),
                    "lang": sub["lang"],
                    "timestamp": sub["timestamp"],
                },
            )
            synced_count += 1
            logger.info("Synced submission %s: %s", sub["id"], sub["title"])
        except Exception:  # noqa: BLE001
            logger.exception("Failed to sync submission %s (%s); will retry next poll",
                              sub["id"], sub.get("title"))

    if synced_count:
        gh.update_readme(state.all_synced())

    return synced_count


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Run a single sync pass and exit")
    args = parser.parse_args()

    settings = load_settings()
    lc = LeetCodeClient(settings.leetcode_session, settings.leetcode_csrf_token,
                         settings.leetcode_username)
    gh = GitHubSync(settings.github_token, settings.github_repo, settings.github_branch,
                     settings.commit_author_name, settings.commit_author_email)
    state = SyncState()

    if args.once:
        run_once(lc, gh, state, settings.submission_fetch_limit)
        return

    logger.info("Starting poll loop (every %ds) for user '%s' -> repo '%s'",
                settings.poll_interval_seconds, settings.leetcode_username, settings.github_repo)
    while True:
        try:
            run_once(lc, gh, state, settings.submission_fetch_limit)
        except Exception:  # noqa: BLE001
            logger.exception("Unexpected error during sync pass; continuing")
        time.sleep(settings.poll_interval_seconds)


if __name__ == "__main__":
    main()
