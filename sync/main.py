"""
Entry point: single-pass sync run, designed to be invoked by the GitHub
Actions workflow on a schedule. There is no loop mode anymore — Actions
provides the scheduling.

Exit code 0: pass completed (whether or not anything new was synced).
Exit code 1: an unrecoverable error occurred (expired auth, GitHub
             permission problem, etc.) — the workflow run will show failed,
             which is intentional: failures should be visible, not silent.

Run:
    python sync/main.py
"""
import logging
import sys
from pathlib import Path
from typing import Any

from config import load_settings
from github_sync import GitHubSync
from leetcode_client import LeetCodeClient
from state import SyncState

import time

LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler(LOG_DIR / "sync.log")],
)
logger = logging.getLogger("leetcode_sync.main")


def _attempt_sync(lc: LeetCodeClient, gh: GitHubSync, state: SyncState, sub: dict[str, Any],
                   escalate_threshold: int) -> bool:
    """Tries to fully sync one submission. Returns True if committed, False
    if code still isn't available from LeetCode yet (will retry next run).
    Lets unexpected errors (network, GitHub API, etc.) propagate to the caller."""
    details = lc.get_submission_details_with_code(sub["id"])

    if not details.get("code"):
        attempts = state.mark_pending(sub["id"], {
            "title": sub["title"],
            "slug": sub["titleSlug"],
            "lang": sub["lang"],
            "timestamp": sub["timestamp"],
        })
        if attempts >= escalate_threshold:
            logger.error(
                "Submission %s (%s) still has no code after %d run(s). Still retrying "
                "automatically, but this is unusual — inspect with the 'Debug submission code' "
                "option in the maintenance workflow if it keeps failing.",
                sub["id"], sub["title"], attempts,
            )
        else:
            logger.warning(
                "Submission %s (%s) has no code yet (attempt %d) — will retry next run.",
                sub["id"], sub["title"], attempts,
            )
        return False

    question = lc.get_question_data(sub["titleSlug"])
    ext = lc.extension_for_lang(sub["lang"])
    gh.sync_solution(sub, details, question, ext)
    state.mark_synced(
        sub["id"], sub["titleSlug"],
        {
            "problem_id": question.get("questionFrontendId") or "0",
            "title": sub["title"],
            "difficulty": question.get("difficulty") or "Unknown",
            "lang": sub["lang"],
            "timestamp": sub["timestamp"],
        },
    )
    logger.info("Synced submission %s: %s", sub["id"], sub["title"])
    return True


def run_once(lc: LeetCodeClient, gh: GitHubSync, state: SyncState, fetch_limit: int,
             commit_delay: float, escalate_threshold: int) -> int:
    """Checks for new + previously-pending submissions and syncs them. Returns count synced."""
    submissions = lc.get_recent_ac_submissions(limit=fetch_limit)
    seen_ids = {str(s["id"]) for s in submissions}

    candidates = [s for s in submissions if not state.is_handled(s["id"])]

    # Pending submissions that have since fallen out of the recent-submissions
    # window still get retried, using metadata captured the first time they
    # were seen — so a long gap between runs doesn't silently drop them.
    for sub_id, rec in state.all_pending().items():
        if sub_id in seen_ids or state.is_handled(sub_id):
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
    candidates.sort(key=lambda s: int(s.get("timestamp") or 0))

    synced_count = 0
    for i, sub in enumerate(candidates):
        try:
            if _attempt_sync(lc, gh, state, sub, escalate_threshold):
                synced_count += 1
                if i < len(candidates) - 1:
                    # Be polite to GitHub's API when committing several
                    # solutions in one run (e.g. catching up after a gap).
                    time.sleep(commit_delay)
        except Exception:  # noqa: BLE001
            logger.exception("Failed to sync submission %s (%s); will retry next run",
                              sub["id"], sub.get("title"))

    if synced_count:
        gh.update_readme(state.all_problems())

    return synced_count


def main() -> None:
    try:
        settings = load_settings()
    except RuntimeError as exc:
        logger.critical(str(exc))
        sys.exit(1)

    try:
        lc = LeetCodeClient(settings.leetcode_session, settings.leetcode_csrf_token,
                             settings.leetcode_username)
        gh = GitHubSync(settings.github_token, settings.github_repo, settings.github_branch)
        state = SyncState()

        logger.info("Starting sync pass for user '%s' -> repo '%s'",
                    settings.leetcode_username, settings.github_repo)

        synced = run_once(
            lc, gh, state,
            fetch_limit=settings.submission_fetch_limit,
            commit_delay=settings.commit_delay_seconds,
            escalate_threshold=settings.pending_escalate_threshold,
        )
        logger.info("Pass complete. Synced %d submission(s) this run.", synced)

    except Exception:  # noqa: BLE001
        # Anything that escapes here is unrecoverable for this run (expired
        # auth after transport retries, GitHub permission errors, etc.) —
        # fail loudly so the Actions run shows red instead of a silent no-op.
        logger.critical("Sync run failed with an unrecoverable error:", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
