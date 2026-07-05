import json
import sqlite3
from pathlib import Path
from uuid import uuid4

from resume_os.merge import MergeResult, merge_candidate
from resume_os.models import EntityKind

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS entities (
  id TEXT PRIMARY KEY, kind TEXT NOT NULL, stable_key TEXT NOT NULL UNIQUE,
  payload_json TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS evidence (
  id TEXT PRIMARY KEY, entity_id TEXT, field_path TEXT NOT NULL,
  source_type TEXT NOT NULL, source_ref TEXT NOT NULL, content TEXT NOT NULL,
  contribution_type TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(entity_id) REFERENCES entities(id)
);
CREATE TABLE IF NOT EXISTS proposals (
  id TEXT PRIMARY KEY, entity_id TEXT NOT NULL, field_path TEXT NOT NULL,
  before_json TEXT NOT NULL, after_json TEXT NOT NULL, reason TEXT NOT NULL,
  evidence_ids_json TEXT NOT NULL, risk_flags_json TEXT NOT NULL, status TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(entity_id) REFERENCES entities(id)
);
CREATE TABLE IF NOT EXISTS conflicts (
  id TEXT PRIMARY KEY, entity_id TEXT NOT NULL, field_path TEXT NOT NULL,
  current_json TEXT NOT NULL, candidate_json TEXT NOT NULL, question TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'open', answer_json TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(entity_id) REFERENCES entities(id)
);
CREATE TABLE IF NOT EXISTS versions (
  id TEXT PRIMARY KEY, entity_id TEXT NOT NULL, snapshot_json TEXT NOT NULL,
  reason TEXT NOT NULL, proposal_id TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(entity_id) REFERENCES entities(id)
);
CREATE TABLE IF NOT EXISTS sources (
  id TEXT PRIMARY KEY, source_type TEXT NOT NULL, source_ref TEXT NOT NULL,
  raw_path TEXT NOT NULL, sha256 TEXT NOT NULL, status TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


class ResumeDatabase:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript(SCHEMA)

    @staticmethod
    def _json(payload: object) -> str:
        return json.dumps(payload, ensure_ascii=False, sort_keys=True)

    def create_entity(self, kind: EntityKind, stable_key: str, payload: dict) -> str:
        entity_id = str(uuid4())
        with self.connection:
            self.connection.execute(
                "INSERT INTO entities(id,kind,stable_key,payload_json) VALUES(?,?,?,?)",
                (entity_id, kind.value, stable_key, self._json(payload)),
            )
        return entity_id

    def find_entity(self, kind: EntityKind, stable_key: str) -> tuple[str, dict] | None:
        row = self.connection.execute(
            "SELECT id,payload_json FROM entities WHERE kind=? AND stable_key=?",
            (kind.value, stable_key),
        ).fetchone()
        return None if row is None else (row["id"], json.loads(row["payload_json"]))

    def get_entity(self, entity_id: str) -> dict:
        row = self.connection.execute(
            "SELECT payload_json FROM entities WHERE id=?", (entity_id,)
        ).fetchone()
        if row is None:
            raise KeyError(entity_id)
        return json.loads(row["payload_json"])

    def replace_entity(
        self, entity_id: str, payload: dict, *, reason: str, proposal_id: str | None = None
    ) -> None:
        version_id = str(uuid4())
        encoded = self._json(payload)
        with self.connection:
            cursor = self.connection.execute(
                "UPDATE entities SET payload_json=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (encoded, entity_id),
            )
            if cursor.rowcount != 1:
                raise KeyError(entity_id)
            self.connection.execute(
                "INSERT INTO versions(id,entity_id,snapshot_json,reason,proposal_id) VALUES(?,?,?,?,?)",
                (version_id, entity_id, encoded, reason, proposal_id),
            )

    def list_versions(self, entity_id: str) -> list[dict]:
        rows = self.connection.execute(
            "SELECT snapshot_json,reason,proposal_id,created_at FROM versions "
            "WHERE entity_id=? ORDER BY created_at,id",
            (entity_id,),
        ).fetchall()
        return [
            {
                "snapshot": json.loads(row["snapshot_json"]),
                "reason": row["reason"],
                "proposal_id": row["proposal_id"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def merge_entity(self, entity_id: str, candidate: dict) -> MergeResult:
        result = merge_candidate(self.get_entity(entity_id), candidate)
        if not result.conflicts:
            self.replace_entity(entity_id, result.merged, reason="candidate merge")
            return result

        with self.connection:
            for conflict in result.conflicts:
                self.connection.execute(
                    "INSERT INTO conflicts("
                    "id,entity_id,field_path,current_json,candidate_json,question"
                    ") VALUES(?,?,?,?,?,?)",
                    (
                        str(uuid4()),
                        entity_id,
                        conflict.field,
                        self._json(conflict.current),
                        self._json(conflict.candidate),
                        conflict.question,
                    ),
                )
        return result

    def list_conflicts(self, entity_id: str) -> list[dict]:
        rows = self.connection.execute(
            "SELECT id,field_path,current_json,candidate_json,question,status,answer_json "
            "FROM conflicts WHERE entity_id=? ORDER BY created_at,id",
            (entity_id,),
        ).fetchall()
        return [
            {
                "id": row["id"],
                "field_path": row["field_path"],
                "current": json.loads(row["current_json"]),
                "candidate": json.loads(row["candidate_json"]),
                "question": row["question"],
                "status": row["status"],
                "answer": None if row["answer_json"] is None else json.loads(row["answer_json"]),
            }
            for row in rows
        ]
