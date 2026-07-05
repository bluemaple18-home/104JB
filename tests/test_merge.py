from pathlib import Path

from resume_os.database import ResumeDatabase
from resume_os.merge import merge_candidate
from resume_os.models import EntityKind


def test_same_project_is_enriched_not_duplicated() -> None:
    current = {"name": "MDreport2", "duration": "約兩個月"}
    candidate = {"name": "MDreport2", "users": "5-10 人"}
    result = merge_candidate(current, candidate)
    assert result.merged == {"name": "MDreport2", "duration": "約兩個月", "users": "5-10 人"}
    assert result.conflicts == []


def test_conflicting_metric_creates_question_and_preserves_current() -> None:
    current = {"monthly_hours_saved": "42-54"}
    candidate = {"monthly_hours_saved": "80"}
    result = merge_candidate(current, candidate)
    assert result.merged["monthly_hours_saved"] == "42-54"
    assert result.conflicts[0].question.startswith("目前記錄為 42-54")


def test_database_persists_conflict_without_changing_entity(tmp_path: Path) -> None:
    db = ResumeDatabase(tmp_path / "resume.sqlite")
    entity_id = db.create_entity(
        EntityKind.PROJECT,
        "project:mdreport2",
        {"name": "MDreport2", "monthly_hours_saved": "42-54"},
    )

    result = db.merge_entity(entity_id, {"monthly_hours_saved": "80", "users": "5-10 人"})

    assert result.conflicts[0].field == "monthly_hours_saved"
    assert db.get_entity(entity_id) == {"name": "MDreport2", "monthly_hours_saved": "42-54"}
    assert db.list_conflicts(entity_id)[0]["candidate"] == "80"


def test_database_replaces_entity_when_merge_has_no_conflict(tmp_path: Path) -> None:
    db = ResumeDatabase(tmp_path / "resume.sqlite")
    entity_id = db.create_entity(EntityKind.PROJECT, "project:mdreport2", {"name": "MDreport2"})

    db.merge_entity(entity_id, {"users": "5-10 人"})

    assert db.get_entity(entity_id)["users"] == "5-10 人"
