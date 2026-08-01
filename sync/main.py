"""
Entry point: polls LeetCode for newly-accepted submissions and syncs each one
to GitHub as soon as it's detected, then keeps the stats README current.

Submissions whose code isn't available yet (LeetCode replication lag, seen
most often on database/SQL problems) are never committed empty — they're
tracked as "pending" and retried automatically on the next poll, with no
manual intervention needed.

Run:
    python main.py            # loop forever at the configured interval
    python main.py --once      # single pass, useful for cron/GitHub Actions
"""
import argparse
import logging
import sys
import time
from pathlib import Path
from typing import Any

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

# After this many consecutive failed poll-cycle attempts for one submission,
# log at ERROR (not just WARNING) so it's impossible to miss in the logs —
# but keep retrying regardless, since it usually still resolves eventually.
PENDING_ESCALATE_THRESHOLD = 5


def _attempt_sync(lc: LeetCodeClient, gh: GitHubSync, state: SyncState, sub: dict[str, Any]) -> bool:
    """Tries to fully sync one submission. Returns True if committed, False
    if code still isn't available from LeetCode yet (will retry next poll).
    Lets unexpected errors (network, GitHub API, etc.) propagate to the caller."""
    details = lc.get_submission_details_with_code(sub["id"])

    if not details.get("code"):
        attempts = state.mark_pending(sub["id"], {
            "title": sub["title"],
            "slug": sub["titleSlug"],
            "lang": sub["lang"],
            "timestamp": sub["timestamp"],
        })
        if attempts >= PENDING_ESCALATE_THRESHOLD:
            logger.error(
                "Submission %s (%s) still has no code after %d poll-cycle attempts. "
                "Still retrying automatically, but this is unusual — inspect with "
                "`python tools/check_submission_code.py %s` if it keeps failing.",
                sub["id"], sub["title"], attempts, sub["id"],
            )
        else:
            logger.warning(
                "Submission %s (%s) has no code yet (attempt %d) — will retry next poll.",
                sub["id"], sub["title"], attempts,
            )
        return False

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
    logger.info("Synced submission %s: %s", sub["id"], sub["title"])
    return True


def run_once(lc: LeetCodeClient, gh: GitHubSync, state: SyncState, fetch_limit: int) -> int:
    """Checks for new + previously-pending submissions and syncs them. Returns count synced."""
    submissions = lc.get_recent_ac_submissions(limit=fetch_limit)
    seen_ids = {str(s["id"]) for s in submissions}

    candidates = [s for s in submissions if not state.is_synced(s["id"])]

    # Pending submissions that have since fallen out of the recent-submissions
    # window (e.g. you solved 20+ more problems since) still get retried,
    # using the metadata captured the first time they were seen.
    for sub_id, rec in state.all_pending().items():
        if sub_id in seen_ids or state.is_synced(sub_id):
            continue
        candidates.append({
            "id": sub_id,
            "title": rec.get("title", "unknown"),
            "titleSlug": rec.get("slug", ""),
            "lang": rec.get("lang", ""),
            "timestamp": rec.get("timestamp", "0"),
        })

    if not candidates:
        logger.info("No new or pending submissions.")
        return 0

    # Oldest first, so commit history reads chronologically.
    candidates.sort(key=lambda s: int(s.get("timestamp", 0)))

    synced_count = 0
    for sub in candidates:
        try:
            if _attempt_sync(lc, gh, state, sub):
                synced_count += 1
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