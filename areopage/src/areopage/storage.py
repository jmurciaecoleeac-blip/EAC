"""Persistance minimale des sessions via SQLite (bibliothèque standard).

Les sessions sont stockées sous leur forme JSON stable ; SQLite sert de
journal durable, pas de modèle relationnel. Aucun chemin n'est codé en
dur : l'appelant fournit le chemin de la base.
"""

import sqlite3
from pathlib import Path

from .models import CouncilSession

_SCHEMA = """
CREATE TABLE IF NOT EXISTS council_sessions (
    id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    document_sha256 TEXT NOT NULL,
    payload TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""


class SessionRepository:
    """Dépôt de sessions adossé à un fichier SQLite fourni par l'appelant."""

    def __init__(self, db_path: str | Path) -> None:
        self._conn = sqlite3.connect(str(db_path))
        self._conn.execute(_SCHEMA)
        self._conn.commit()

    def save(self, session: CouncilSession) -> None:
        self._conn.execute(
            """
            INSERT INTO council_sessions (id, status, document_sha256, payload, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                status = excluded.status,
                payload = excluded.payload,
                updated_at = excluded.updated_at
            """,
            (
                str(session.id),
                session.status.value,
                session.document.sha256,
                session.to_stable_json(),
                session.updated_at.isoformat(),
            ),
        )
        self._conn.commit()

    def get(self, session_id: str) -> CouncilSession | None:
        row = self._conn.execute(
            "SELECT payload FROM council_sessions WHERE id = ?", (session_id,)
        ).fetchone()
        if row is None:
            return None
        return CouncilSession.from_json(row[0])

    def list_ids(self) -> list[str]:
        rows = self._conn.execute(
            "SELECT id FROM council_sessions ORDER BY updated_at"
        ).fetchall()
        return [r[0] for r in rows]

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "SessionRepository":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()
