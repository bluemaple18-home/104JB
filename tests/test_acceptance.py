import json
from pathlib import Path

from resume_os.cli import run

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text("utf-8"))


def _create_fixture_profile(workspace: Path, fixture_name: str) -> str:
    fixture = _load(fixture_name)
    run(
        ["profile", "create", fixture["slug"], "--display-name", fixture["display_name"]],
        workspace=workspace,
    )
    run(["profile", "select", fixture["slug"]], workspace=workspace)
    entity = fixture["entity"]
    result = run(
        [
            "entity",
            "add",
            entity["kind"],
            entity["stable_key"],
            "--payload-json",
            json.dumps(entity["payload"], ensure_ascii=False),
        ],
        workspace=workspace,
    )
    return result.stdout_json["entity_id"]


def test_two_profiles_never_share_entities(tmp_path: Path) -> None:
    _create_fixture_profile(tmp_path, "matt_candidate.json")
    matt_output = run(["export", "104"], workspace=tmp_path).stdout
    _create_fixture_profile(tmp_path, "friend_candidate.json")
    friend_output = run(["export", "104"], workspace=tmp_path).stdout

    assert "Synthetic Friend Company" not in matt_output
    assert "MDreport2 Synthetic" not in friend_output


def test_rejected_and_blocked_proposals_never_reach_export(tmp_path: Path) -> None:
    entity_id = _create_fixture_profile(tmp_path, "matt_candidate.json")
    blocked = run(
        [
            "proposal",
            "create",
            entity_id,
            "role",
            "--after-json",
            json.dumps("獨立開發完整機器學習架構", ensure_ascii=False),
            "--reason",
            "改寫角色",
        ],
        workspace=tmp_path,
    )
    rejected = run(
        [
            "proposal",
            "create",
            entity_id,
            "result",
            "--after-json",
            json.dumps("提升 80%", ensure_ascii=False),
            "--reason",
            "加入數字",
        ],
        workspace=tmp_path,
    )
    run(["proposal", "reject", rejected.stdout_json["id"]], workspace=tmp_path)

    output = run(["export", "104"], workspace=tmp_path).stdout
    assert blocked.stdout_json["status"] == "blocked"
    assert "機器學習架構" not in output
    assert "80%" not in output


def test_accepted_synthetic_proposal_reaches_export_and_evaluation(tmp_path: Path) -> None:
    entity_id = _create_fixture_profile(tmp_path, "matt_candidate.json")
    evidence = run(
        [
            "evidence",
            "add",
            entity_id,
            "result",
            "--source-type",
            "interview",
            "--source-ref",
            "synthetic-answer",
            "--content",
            "減少每月 42 小時人工作業",
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
            json.dumps("減少每月 42 小時人工作業", ensure_ascii=False),
            "--reason",
            "補齊成果證據",
            "--evidence-id",
            evidence.stdout_json["evidence_id"],
        ],
        workspace=tmp_path,
    )
    run(["proposal", "accept", proposal.stdout_json["id"]], workspace=tmp_path)

    output = run(["export", "104"], workspace=tmp_path).stdout
    evaluation = run(["evaluate"], workspace=tmp_path).stdout_json["evaluation"]

    assert "減少每月 42 小時人工作業" in output
    assert set(evaluation) == {
        "parseability",
        "role_clarity",
        "outcome_evidence",
        "skills",
        "credibility",
    }
    assert "total" not in evaluation
