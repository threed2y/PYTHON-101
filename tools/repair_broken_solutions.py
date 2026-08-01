"""
Repair tool: re-fetches and re-commits any solution file that was already
synced with empty/missing code (from before the retry-on-empty-code fix).

Run once after upgrading to the retry-aware version of the sync tool, to
backfill anything that got committed broken before this fix existed.

Usage:
    python tools/repair_broken_solutions.py            # scan + repair everything in state
    python tools/repair_broken_solutions.py <sub_id>    # repair one specific submission
"""
import json
import os
import sys
from pathlib import Path

SYNC_DIR = Path(__file__).parent.parent / "sync"
sys.path.insert(0, str(SYNC_DIR))

from dotenv import load_dotenv
load_dotenv(SYNC_DIR / ".env")

from config import load_settings  # noqa: E402
from github_sync import GitHubSync, _pad_id  # noqa: E402
from leetcode_client import LeetCodeClient  # noqa: E402
from state import SyncState  # noqa: E402


def is_broken(gh: GitHubSync, difficulty: str, padded_id: str, slug: str, ext: str) -> bool:
    """A file is considered broken if it's just the one-line link header
    with no actual code after it."""
    path = f"solutions/{difficulty.lower()}/{padded_id}-{slug}/solution.{ext}"
    try:
        contents = gh.repo.get_contents(path, ref=gh.branch)
        text = contents.decoded_content.decode("utf-8", errors="replace")
    except Exception:
        return True  # missing entirely counts as broken too
    # Header is one line + blank line; anything beyond that is real code.
    body = "\n".join(text.splitlines()[2:]).strip()
    return len(body) == 0


def main() -> None:
    settings = load_settings()
    lc = LeetCodeClient(settings.leetcode_session, settings.leetcode_csrf_token,
                         settings.leetcode_username)
    gh = GitHubSync(settings.github_token, settings.github_repo, settings.github_branch,
                     settings.commit_author_name, settings.commit_author_email)
    state = SyncState()

    only_id = sys.argv[1] if len(sys.argv) > 1 else None
    synced = state.all_synced()
    targets = {only_id: synced[only_id]} if only_id else synced

    repaired, skipped = 0, 0
    for sub_id, rec in targets.items():
        difficulty = rec.get("difficulty", "Unknown")
        slug = rec.get("slug", "")
        lang = rec.get("lang", "")
        ext = lc.extension_for_lang(lang)
        padded_id = _pad_id(rec.get("problem_id", "0"))

        if not is_broken(gh, difficulty, padded_id, slug, ext):
            skipped += 1
            continue

        print(f"Repairing {sub_id} ({rec.get('title')})...")
        details = lc.get_submission_details_with_code(sub_id, max_attempts=5, base_delay=3.0)
        if not details.get("code"):
            print(f"  still no code available from LeetCode for {sub_id}; skipping for now")
            continue

        question = lc.get_question_data(slug)
        sub = {
            "id": sub_id,
            "title": rec.get("title"),
            "titleSlug": slug,
            "lang": lang,
            "timestamp": rec.get("timestamp", "0"),
        }
        gh.sync_solution(sub, details, question, ext)
        repaired += 1
        print(f"  fixed.")

    gh.update_readme(state.all_synced())
    print(f"\nDone. Repaired: {repaired}, already fine: {skipped}")


if __name__ == "__main__":
    main()