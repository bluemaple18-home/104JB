from resume_os.evaluation import evaluate_resume
from resume_os.export_104 import render_104


def test_render_104_keeps_pm_and_ai_contribution_truthful() -> None:
    entities = [
        {
            "kind": "project",
            "name": "NEW-TOP10",
            "role": "以 PM 方式定義需求、規則與驗收，透過 AI 協作完成實作",
            "result": "每日選股、歷史回測與模擬追蹤",
        }
    ]
    output = render_104(entities)
    assert "以 PM 方式" in output
    assert "獨立開發機器學習架構" not in output


def test_render_104_omits_empty_sections() -> None:
    output = render_104([{"kind": "project", "name": "Synthetic Project"}])

    assert "專案成果" in output
    assert "工作經歷" not in output
    assert "學歷" not in output


def test_render_104_does_not_emit_internal_capability_section() -> None:
    output = render_104(
        [
            {"kind": "capability", "name": "Synthetic Capability Profile"},
            {"kind": "project", "name": "Synthetic Project"},
        ]
    )

    assert "Synthetic Capability Profile" not in output
    assert "Synthetic Project" in output


def test_evaluation_has_five_dimensions_and_no_total_score() -> None:
    result = evaluate_resume([{"id": "project-1", "kind": "project", "name": "MDreport2", "evidence_count": 3}])
    assert set(result) == {
        "parseability",
        "role_clarity",
        "outcome_evidence",
        "skills",
        "credibility",
    }
    assert "total" not in result
    assert all(set(item) == {"status", "reasons", "entity_ids"} for item in result.values())
    assert all(item["reasons"] for item in result.values())
