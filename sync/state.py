"""
Local JSON state store.

Tracks which submission IDs have already been synced to GitHub so the poller
never double-commits, even across restarts. Also stores enough metadata about
each solved problem to regenerate the stats README without re-querying LeetCode.
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
                return json.load(f)
        return {"synced": {}}

    def _save(self) -> None:
        tmp_path = self.path.with_suffix(".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, sort_keys=True)
        os.replace(tmp_path, self.path)  # atomic on POSIX

    def is_synced(self, submission_id: str) -> bool:
        return str(submission_id) in self._data["synced"]

    def mark_synced(self, submission_id: str, record: dict[str, Any]) -> None:
        self._data["synced"][str(submission_id)] = record
        self._save()

    def all_synced(self) -> dict[str, Any]:
        return self._data["synced"]
