from pathlib import Path

import pytest

from resume_os.database import ResumeDatabase
from resume_os.evidence import unsupported_claims
from resume_os.models import EntityKind, Evidence
from resume_os.proposals import ProposalService


def test_ai_implementation_cannot_be_rewritten_as_personal_engineering() -> None:
    before = "以 PM 方式透過 AI 協作完成產品"
    after = "獨立設計並開發完整機器學習架構"
    evidence = ["contribution_type=owner_decision", "contribution_type=ai_assisted_implementation"]
    assert "engineering_ownership" in unsupported_claims(before, after, evidence)


def test_new_metric_without_evidence_is_blocked() -> None:
    assert "unsupported_number" in unsupported_claims("改善流程", "提升效率 80%", [])


@pytest.mark.parametrize(
    ("field_path", "after", "risk"),
    [
        ("skills", "Python", "unsupported_skill"),
        ("certification", "PMP", "unsupported_certification"),
        ("job_title", "資深產品經理", "unsupported_title"),
        ("company", "Example Corp", "unsupported_company"),
        ("start_date", "2026-01", "unsupported_date"),
    ],
)
def test_high_risk_field_without_matching_evidence_is_blocked(
    field_path: str, after: str, risk: str
) -> None:
    assert risk in unsupported_claims("", after, [], field_path=field_path)


def test_accept_updates_canonical_and_version(tmp_path: Path) -> None:
    db = ResumeDatabase(tmp_path / "resume.sqlite")
    entity_id = db.create_entity(EntityKind.PROJECT, "project:demo", {"result": "改善流程"})
    evidence_id = db.add_evidence(
        Evidence(
            entity_id=entity_id,
            field_path="result",
            source_type="interview",
            source_ref="answer-1",
            content="每月節省 42 小時",
        )
    )
    service = ProposalService(db)
    proposal = service.create(
        entity_id,
        "result",
        "每月節省 42 小時",
        reason="補齊可驗證成果",
        evidence_ids=[evidence_id],
    )

    assert proposal["status"] == "pending"
    accepted = service.accept(proposal["id"])

    assert accepted["status"] == "accepted"
    assert db.get_entity(entity_id)["result"] == "每月節省 42 小時"
    assert db.list_versions(entity_id)[0]["proposal_id"] == proposal["id"]


def test_reject_does_not_update_canonical(tmp_path: Path) -> None:
    db = ResumeDatabase(tmp_path / "resume.sqlite")
    entity_id = db.create_entity(EntityKind.PROJECT, "project:demo", {"role": "PM"})
    evidence_id = db.add_evidence(
        Evidence(
            entity_id=entity_id,
            field_path="role",
            source_type="interview",
            source_ref="answer-1",
            content="產品經理",
        )
    )
    service = ProposalService(db)
    proposal = service.create(
        entity_id, "role", "產品經理", reason="明確角色", evidence_ids=[evidence_id]
    )

    service.reject(proposal["id"])

    assert db.get_entity(entity_id)["role"] == "PM"
    assert service.get(proposal["id"])["status"] == "rejected"


def test_blocked_proposal_cannot_be_accepted(tmp_path: Path) -> None:
    db = ResumeDatabase(tmp_path / "resume.sqlite")
    entity_id = db.create_entity(EntityKind.PROJECT, "project:demo", {"result": "改善流程"})
    service = ProposalService(db)

    proposal = service.create(
        entity_id, "result", "提升效率 80%", reason="強化成果", evidence_ids=[]
    )

    assert proposal["status"] == "blocked"
    with pytest.raises(ValueError, match="blocked"):
        service.accept(proposal["id"])
    assert db.get_entity(entity_id)["result"] == "改善流程"


def test_edited_text_runs_guard_again_before_acceptance(tmp_path: Path) -> None:
    db = ResumeDatabase(tmp_path / "resume.sqlite")
    entity_id = db.create_entity(EntityKind.PROJECT, "project:demo", {"result": "改善流程"})
    service = ProposalService(db)
    blocked = service.create(
        entity_id, "result", "提升效率 80%", reason="強化成果", evidence_ids=[]
    )

    edited = service.edit(blocked["id"], "改善流程清晰度")

    assert edited["status"] == "edited"
    service.accept(edited["id"])
    assert db.get_entity(entity_id)["result"] == "改善流程清晰度"
