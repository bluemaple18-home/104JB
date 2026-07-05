import json
from pathlib import Path

from resume_os.cli import run
from resume_os.database import ResumeDatabase
from resume_os.models import EntityKind


def test_cli_blocks_write_without_active_profile(tmp_path: Path) -> None:
    result = run(["proposal", "list"], workspace=tmp_path)
    assert result.exit_code == 2
    assert "select a profile" in result.stderr
    assert result.stdout_json["error_code"] == "NO_ACTIVE_PROFILE"


def test_cli_profile_source_to_export_flow(tmp_path: Path) -> None:
    assert run(["profile", "create", "matt", "--display-name", "Matt"], workspace=tmp_path).exit_code == 0
    assert run(["profile", "select", "matt"], workspace=tmp_path).exit_code == 0
    source = tmp_path / "resume.txt"
    source.write_text("專案經理｜負責 DSP 與 SSP 報表", encoding="utf-8")
    imported = run(["source", "import-text", str(source)], workspace=tmp_path)
    assert imported.exit_code == 0
    assert imported.stdout_json["status"] == "ready"
    assert run(["status"], workspace=tmp_path).stdout_json["active_profile"] == "matt"


def test_cli_entity_proposal_approval_and_export(tmp_path: Path) -> None:
    run(["profile", "create", "matt", "--display-name", "Matt"], workspace=tmp_path)
    run(["profile", "select", "matt"], workspace=tmp_path)
    created = run(
        [
            "entity",
            "add",
            "project",
            "project:demo",
            "--payload-json",
            json.dumps({"name": "Synthetic Project", "role": "PM"}, ensure_ascii=False),
        ],
        workspace=tmp_path,
    )
    entity_id = created.stdout_json["entity_id"]
    evidence = run(
        [
            "evidence",
            "add",
            entity_id,
            "result",
            "--source-type",
            "interview",
            "--source-ref",
            "answer-1",
            "--content",
            "每月節省 42 小時",
        ],
        workspace=tmp_path,
    )
    proposal = run(
        [
            "proposal",
            "create",
            entity_id,
            "result",
            "--after-json",
            json.dumps("每月節省 42 小時", ensure_ascii=False),
            "--reason",
            "補齊成果",
            "--evidence-id",
            evidence.stdout_json["evidence_id"],
        ],
        workspace=tmp_path,
    )

    accepted = run(["proposal", "accept", proposal.stdout_json["id"]], workspace=tmp_path)
    exported = run(["export", "104"], workspace=tmp_path)

    assert accepted.stdout_json["status"] == "accepted"
    assert "每月節省 42 小時" in exported.stdout
    assert run(["entity", "list"], workspace=tmp_path).stdout_json["entities"][0]["kind"] == "project"


def test_cli_answers_conflict_before_changing_canonical(tmp_path: Path) -> None:
    run(["profile", "create", "matt", "--display-name", "Matt"], workspace=tmp_path)
    run(["profile", "select", "matt"], workspace=tmp_path)
    db = ResumeDatabase(tmp_path / "profiles" / "matt" / "resume.sqlite")
    entity_id = db.create_entity(EntityKind.PROJECT, "project:demo", {"users": "5"})
    db.merge_entity(entity_id, {"users": "10"})
    conflict_id = db.list_conflicts(entity_id)[0]["id"]

    answered = run(
        ["conflict", "answer", conflict_id, "--value-json", json.dumps("10")], workspace=tmp_path
    )

    assert answered.stdout_json["status"] == "resolved"
    assert ResumeDatabase(tmp_path / "profiles" / "matt" / "resume.sqlite").get_entity(entity_id)["users"] == "10"
