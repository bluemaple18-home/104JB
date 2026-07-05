import json
from uuid import uuid4

from resume_os.database import ResumeDatabase
from resume_os.evidence import unsupported_claims


class ProposalService:
    def __init__(self, database: ResumeDatabase) -> None:
        self.database = database

    def _evidence_text(self, evidence_ids: list[str]) -> list[str]:
        return [
            f"{item['content']} contribution_type={item['contribution_type']}"
            for item in self.database.get_evidence(evidence_ids)
        ]

    def create(
        self,
        entity_id: str,
        field_path: str,
        after: object,
        *,
        reason: str,
        evidence_ids: list[str],
    ) -> dict:
        payload = self.database.get_entity(entity_id)
        field = field_path.rsplit(".", 1)[-1]
        before = payload.get(field)
        risks = unsupported_claims(
            "" if before is None else str(before),
            str(after),
            self._evidence_text(evidence_ids),
            field_path=field_path,
        )
        proposal_id = str(uuid4())
        status = "blocked" if risks else "pending"
        with self.database.connection:
            self.database.connection.execute(
                "INSERT INTO proposals("
                "id,entity_id,field_path,before_json,after_json,reason,"
                "evidence_ids_json,risk_flags_json,status"
                ") VALUES(?,?,?,?,?,?,?,?,?)",
                (
                    proposal_id,
                    entity_id,
                    field_path,
                    self.database._json(before),
                    self.database._json(after),
                    reason,
                    self.database._json(evidence_ids),
                    self.database._json(risks),
                    status,
                ),
            )
        return self.get(proposal_id)

    def get(self, proposal_id: str) -> dict:
        row = self.database.connection.execute(
            "SELECT * FROM proposals WHERE id=?", (proposal_id,)
        ).fetchone()
        if row is None:
            raise KeyError(proposal_id)
        return {
            "id": row["id"],
            "entity_id": row["entity_id"],
            "field_path": row["field_path"],
            "before": json.loads(row["before_json"]),
            "after": json.loads(row["after_json"]),
            "reason": row["reason"],
            "evidence_ids": json.loads(row["evidence_ids_json"]),
            "risk_flags": json.loads(row["risk_flags_json"]),
            "status": row["status"],
        }

    def list(self) -> list[dict]:
        rows = self.database.connection.execute(
            "SELECT id FROM proposals ORDER BY created_at,id"
        ).fetchall()
        return [self.get(row["id"]) for row in rows]

    def accept(self, proposal_id: str) -> dict:
        proposal = self.get(proposal_id)
        if proposal["status"] not in {"pending", "edited"}:
            raise ValueError(f"cannot accept {proposal['status']} proposal")
        payload = self.database.get_entity(proposal["entity_id"])
        field = proposal["field_path"].rsplit(".", 1)[-1]
        payload[field] = proposal["after"]
        encoded = self.database._json(payload)
        with self.database.connection:
            self.database.connection.execute(
                "UPDATE entities SET payload_json=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (encoded, proposal["entity_id"]),
            )
            self.database.connection.execute(
                "INSERT INTO versions(id,entity_id,snapshot_json,reason,proposal_id) "
                "VALUES(?,?,?,?,?)",
                (str(uuid4()), proposal["entity_id"], encoded, proposal["reason"], proposal_id),
            )
            self.database.connection.execute(
                "UPDATE proposals SET status='accepted' WHERE id=?", (proposal_id,)
            )
        return self.get(proposal_id)

    def reject(self, proposal_id: str) -> dict:
        proposal = self.get(proposal_id)
        if proposal["status"] == "accepted":
            raise ValueError("cannot reject accepted proposal")
        with self.database.connection:
            self.database.connection.execute(
                "UPDATE proposals SET status='rejected' WHERE id=?", (proposal_id,)
            )
        return self.get(proposal_id)

    def edit(self, proposal_id: str, after: object) -> dict:
        proposal = self.get(proposal_id)
        if proposal["status"] in {"accepted", "rejected"}:
            raise ValueError(f"cannot edit {proposal['status']} proposal")
        risks = unsupported_claims(
            "" if proposal["before"] is None else str(proposal["before"]),
            str(after),
            self._evidence_text(proposal["evidence_ids"]),
            field_path=proposal["field_path"],
        )
        status = "blocked" if risks else "edited"
        with self.database.connection:
            self.database.connection.execute(
                "UPDATE proposals SET after_json=?,risk_flags_json=?,status=? WHERE id=?",
                (
                    self.database._json(after),
                    self.database._json(risks),
                    status,
                    proposal_id,
                ),
            )
        return self.get(proposal_id)
