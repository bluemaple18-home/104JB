import json
import sqlite3
from pathlib import Path
from uuid import uuid4

from resume_os.merge import MergeResult, merge_candidate
from resume_os.models import EntityKind, Evidence

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

    def add_evidence(self, evidence: Evidence) -> str:
        evidence_id = str(uuid4())
        with self.connection:
            self.connection.execute(
                "INSERT INTO evidence("
                "id,entity_id,field_path,source_type,source_ref,content,contribution_type"
                ") VALUES(?,?,?,?,?,?,?)",
                (
                    evidence_id,
                    evidence.entity_id,
                    evidence.field_path,
                    evidence.source_type,
                    evidence.source_ref,
                    evidence.content,
                    evidence.contribution_type,
                ),
            )
        return evidence_id

    def get_evidence(self, evidence_ids: list[str]) -> list[dict]:
        if not evidence_ids:
            return []
        placeholders = ",".join("?" for _ in evidence_ids)
        rows = self.connection.execute(
            f"SELECT * FROM evidence WHERE id IN ({placeholders})", evidence_ids
        ).fetchall()
        by_id = {row["id"]: dict(row) for row in rows}
        return [by_id[evidence_id] for evidence_id in evidence_ids if evidence_id in by_id]

    def list_entities(self) -> list[dict]:
        rows = self.connection.execute(
            "SELECT e.id,e.kind,e.stable_key,e.payload_json,COUNT(v.id) AS evidence_count "
            "FROM entities e LEFT JOIN evidence v ON v.entity_id=e.id "
            "GROUP BY e.id ORDER BY e.created_at,e.id"
        ).fetchall()
        return [
            {
                "id": row["id"],
                "kind": row["kind"],
                "stable_key": row["stable_key"],
                **json.loads(row["payload_json"]),
                "evidence_count": row["evidence_count"],
            }
            for row in rows
        ]

    def add_source(
        self,
        *,
        source_type: str,
        source_ref: str,
        raw_path: str,
        sha256: str,
        status: str,
    ) -> str:
        source_id = str(uuid4())
        with self.connection:
            self.connection.execute(
                "INSERT INTO sources(id,source_type,source_ref,raw_path,sha256,status) "
                "VALUES(?,?,?,?,?,?)",
                (source_id, source_type, source_ref, raw_path, sha256, status),
            )
        return source_id

    def list_sources(self) -> list[dict]:
        return [
            dict(row)
            for row in self.connection.execute(
                "SELECT * FROM sources ORDER BY created_at,id"
            ).fetchall()
        ]

    def answer_conflict(self, conflict_id: str, answer: object) -> dict:
        row = self.connection.execute(
            "SELECT * FROM conflicts WHERE id=?", (conflict_id,)
        ).fetchone()
        if row is None:
            raise KeyError(conflict_id)
        if row["status"] != "open":
            raise ValueError("conflict is already resolved")
        payload = self.get_entity(row["entity_id"])
        payload[row["field_path"].rsplit(".", 1)[-1]] = answer
        encoded = self._json(payload)
        with self.connection:
            self.connection.execute(
                "UPDATE entities SET payload_json=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (encoded, row["entity_id"]),
            )
            self.connection.execute(
                "INSERT INTO versions(id,entity_id,snapshot_json,reason,proposal_id) "
                "VALUES(?,?,?,?,NULL)",
                (str(uuid4()), row["entity_id"], encoded, "conflict resolved"),
            )
            self.connection.execute(
                "UPDATE conflicts SET status='resolved',answer_json=? WHERE id=?",
                (self._json(answer), conflict_id),
            )
        return {"id": conflict_id, "status": "resolved", "answer": answer}
