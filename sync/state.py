"""
Local JSON state store.

Tracks which submission IDs have already been synced to GitHub so the poller
never double-commits, even across restarts. Also tracks "pending" submissions
that were detected but couldn't be synced yet (e.g. code not available from
LeetCode yet) so they're retried on the next poll instead of being silently
dropped or committed incomplete.
"""
import json
import os
from pathlib import Path
from typing import Any

STATE_PATH = Path(__file__).parent / "sync_state.json"


class SyncState:
    def __init__(self, path: Path = STATE_PATH):
        self.path = path
        self._data: dict[str, Any] = self._load()

    def _load(self) -> dict[str, Any]:
        if self.path.exists():
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {}
        data.setdefault("synced", {})
        data.setdefault("pending", {})  # submission_id -> {"attempts": int, ...}
        return data

    def _save(self) -> None:
        tmp_path = self.path.with_suffix(".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, sort_keys=True)
        os.replace(tmp_path, self.path)  # atomic on POSIX

    def is_synced(self, submission_id: str) -> bool:
        return str(submission_id) in self._data["synced"]

    def mark_synced(self, submission_id: str, record: dict[str, Any]) -> None:
        submission_id = str(submission_id)
        self._data["synced"][submission_id] = record
        self._data["pending"].pop(submission_id, None)
        self._save()

    def mark_pending(self, submission_id: str, record: dict[str, Any]) -> int:
        """Records a failed sync attempt for later retry. Returns the new attempt count."""
        submission_id = str(submission_id)
        existing = self._data["pending"].get(submission_id, {"attempts": 0})
        existing["attempts"] = existing.get("attempts", 0) + 1
        existing.update({k: v for k, v in record.items() if k != "attempts"})
        self._data["pending"][submission_id] = existing
        self._save()
        return existing["attempts"]

    def pending_attempts(self, submission_id: str) -> int:
        return self._data["pending"].get(str(submission_id), {}).get("attempts", 0)

    def all_synced(self) -> dict[str, Any]:
        return self._data["synced"]

    def all_pending(self) -> dict[str, Any]:
        return self._data["pending"]