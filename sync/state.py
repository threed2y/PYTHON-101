"""
Local JSON state store (sync_state.json, committed back to the repo by the
workflow after each run — Actions runners are ephemeral, so this is the
only thing that persists between runs).

Schema v2:
{
  "version": 2,
  "handled_submission_ids": ["111", "222"],
  "problems": {"<slug>": {"submission_id", "problem_id", "title",
                            "difficulty", "lang", "timestamp"}},
  "pending": {"<submission_id>": {"attempts", "title", "slug", "lang", "timestamp"}}
}

`problems` is keyed by slug (not submission ID), so resolving a problem a
second time overwrites its entry instead of producing a duplicate row in
the generated stats README. `handled_submission_ids` is what prevents the
same submission from being reprocessed on every future run.

Automatically upgrades the old v1 schema ({"synced": {...}, "pending": {...}}
keyed by submission ID) on load, so existing repos don't lose history when
this tool is updated.
"""
import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger("leetcode_sync.state")

STATE_PATH = Path(__file__).parent / "sync_state.json"
CURRENT_VERSION = 2


class SyncState:
    def __init__(self, path: Path = STATE_PATH):
        self.path = path
        self._data: dict[str, Any] = self._load()

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return self._empty()

        with open(self.path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        if raw.get("version") == CURRENT_VERSION:
            raw.setdefault("handled_submission_ids", [])
            raw.setdefault("problems", {})
            raw.setdefault("pending", {})
            return raw

        return self._migrate_v1(raw)

    @staticmethod
    def _empty() -> dict[str, Any]:
        return {"version": CURRENT_VERSION, "handled_submission_ids": [], "problems": {}, "pending": {}}

    @staticmethod
    def _migrate_v1(raw: dict[str, Any]) -> dict[str, Any]:
        legacy_synced = raw.get("synced", {})
        legacy_pending = raw.get("pending", {})

        problems: dict[str, Any] = {}
        handled: list[str] = []
        for sub_id, rec in legacy_synced.items():
            slug = rec.get("slug")
            if not slug:
                continue
            problems[slug] = {
                "submission_id": sub_id,
                "problem_id": rec.get("problem_id", "0"),
                "title": rec.get("title", "unknown"),
                "difficulty": rec.get("difficulty", "Unknown"),
                "lang": rec.get("lang", ""),
                "timestamp": rec.get("timestamp", "0"),
            }
            handled.append(sub_id)

        if legacy_synced or legacy_pending:
            logger.info(
                "Migrated legacy v1 state to v2: %d synced problem(s), %d pending. "
                "No history was lost.",
                len(problems), len(legacy_pending),
            )

        return {
            "version": CURRENT_VERSION,
            "handled_submission_ids": handled,
            "problems": problems,
            "pending": legacy_pending,
        }

    def _save(self) -> None:
        tmp_path = self.path.with_suffix(".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, sort_keys=True)
        os.replace(tmp_path, self.path)  # atomic on POSIX

    # --- handled / synced ---------------------------------------------

    def is_handled(self, submission_id: Any) -> bool:
        return str(submission_id) in self._data["handled_submission_ids"]

    def mark_synced(self, submission_id: Any, slug: str, record: dict[str, Any]) -> None:
        submission_id = str(submission_id)
        record = dict(record)
        record["submission_id"] = submission_id
        self._data["problems"][slug] = record
        if submission_id not in self._data["handled_submission_ids"]:
            self._data["handled_submission_ids"].append(submission_id)
        self._data["pending"].pop(submission_id, None)
        self._save()

    def all_problems(self) -> dict[str, Any]:
        return self._data["problems"]

    # --- pending ---------------------------------------------------------

    def mark_pending(self, submission_id: Any, record: dict[str, Any]) -> int:
        """Records a failed sync attempt for later retry. Returns the new attempt count."""
        submission_id = str(submission_id)
        existing = self._data["pending"].get(submission_id, {"attempts": 0})
        existing["attempts"] = existing.get("attempts", 0) + 1
        existing.update({k: v for k, v in record.items() if k != "attempts"})
        self._data["pending"][submission_id] = existing
        self._save()
        return existing["attempts"]

    def pending_attempts(self, submission_id: Any) -> int:
        return self._data["pending"].get(str(submission_id), {}).get("attempts", 0)

    def all_pending(self) -> dict[str, Any]:
        return self._data["pending"]
