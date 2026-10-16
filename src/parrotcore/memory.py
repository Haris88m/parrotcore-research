from __future__ import annotations

import sqlite3
import threading
from pathlib import Path


class MemoryStore:
    def __init__(self, path: str | Path = ":memory:") -> None:
        self.path = str(path)
        self._lock = threading.RLock()
        self.db = sqlite3.connect(self.path, check_same_thread=False)
        with self._lock:
            self.db.execute("""
                CREATE TABLE IF NOT EXISTS associations (
                    trigger TEXT PRIMARY KEY,
                    response TEXT NOT NULL
                )
            """)
            self.db.commit()

    def teach(self, trigger: str, response: str) -> None:
        trigger = trigger.strip().lower()
        response = response.strip()
        if not trigger or not response:
            raise ValueError("trigger and response must be non-empty")
        with self._lock:
            self.db.execute(
                "INSERT INTO associations(trigger,response) VALUES(?,?) "
                "ON CONFLICT(trigger) DO UPDATE SET response=excluded.response",
                (trigger, response),
            )
            self.db.commit()

    def recall(self, trigger: str) -> str | None:
        with self._lock:
            row = self.db.execute(
                "SELECT response FROM associations WHERE trigger=?", (trigger.strip().lower(),)
            ).fetchone()
        return None if row is None else str(row[0])

    def all(self) -> dict[str, str]:
        with self._lock:
            rows = self.db.execute("SELECT trigger,response FROM associations ORDER BY trigger").fetchall()
        return {str(k): str(v) for k, v in rows}

    def close(self) -> None:
        with self._lock:
            db = getattr(self, "db", None)
            if db is not None:
                db.close()
                self.db = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
