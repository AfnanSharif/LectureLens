from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class FeedbackRepository:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
                    comment TEXT NOT NULL DEFAULT '',
                    quiz_score INTEGER,
                    created_at TEXT NOT NULL
                )"""
            )
            connection.execute(
                """CREATE TABLE IF NOT EXISTS learning_packs (
                    session_id TEXT PRIMARY KEY,
                    payload_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )"""
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=5)
        connection.row_factory = sqlite3.Row
        return connection

    def add(self, session_id: str, rating: int, comment: str = "", quiz_score: int | None = None) -> int:
        if not session_id.strip():
            raise ValueError("session_id is required")
        if rating not in range(1, 6):
            raise ValueError("rating must be between 1 and 5")
        if len(comment) > 2000:
            raise ValueError("comment must be 2,000 characters or fewer")
        with self._connect() as connection:
            cursor = connection.execute(
                "INSERT INTO feedback(session_id, rating, comment, quiz_score, created_at) VALUES (?, ?, ?, ?, ?)",
                (session_id, rating, comment.strip(), quiz_score, datetime.now(timezone.utc).isoformat()),
            )
            return int(cursor.lastrowid)

    def summary(self) -> dict[str, float | int]:
        with self._connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS count, COALESCE(AVG(rating), 0) AS average FROM feedback").fetchone()
        return {"count": int(row["count"]), "average_rating": round(float(row["average"]), 2)}

    def save_pack(self, session_id: str, payload: dict) -> None:
        if not session_id.strip():
            raise ValueError("session_id is required")
        serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        with self._connect() as connection:
            connection.execute(
                """INSERT INTO learning_packs(session_id, payload_json, updated_at) VALUES (?, ?, ?)
                   ON CONFLICT(session_id) DO UPDATE SET payload_json=excluded.payload_json, updated_at=excluded.updated_at""",
                (session_id, serialized, datetime.now(timezone.utc).isoformat()),
            )

    def load_pack(self, session_id: str) -> dict | None:
        with self._connect() as connection:
            row = connection.execute("SELECT payload_json FROM learning_packs WHERE session_id = ?", (session_id,)).fetchone()
        return json.loads(row["payload_json"]) if row else None
