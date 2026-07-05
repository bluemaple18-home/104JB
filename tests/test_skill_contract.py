from pathlib import Path


def test_skill_requires_profile_evidence_and_human_approval() -> None:
    text = Path(".codex/skills/resume-os/SKILL.md").read_text("utf-8")
    assert "profile" in text
    assert "Evidence Guard" in text
    assert "一次只問一個關鍵問題" in text
    assert "不得直接寫入 Master Resume" in text
    assert "修改前" in text and "修改後" in text and "修改理由" in text


def test_skill_keeps_llm_outside_deterministic_mutations() -> None:
    text = Path(".codex/skills/resume-os/SKILL.md").read_text("utf-8")
    assert "LLM" in text
    assert "deterministic" in text
    assert "ai_assisted_implementation" in text


def test_skill_synthesizes_capabilities_before_resume_rewriting() -> None:
    text = Path(".codex/skills/resume-os/SKILL.md").read_text("utf-8")
    assert "讀完整份原始履歷" in text
    assert "Capability Profile" in text
    assert "至少兩段不同經歷" in text
    assert "不得只從職稱、工具或單一工作項目" in text
    assert "Capability Profile 未核准前，不得開始履歷改寫" in text


def test_capability_workflow_requires_evidence_and_profile_local_storage() -> None:
    text = Path(".codex/skills/resume-os/references/workflow.md").read_text("utf-8")
    assert "capability:core" in text
    assert "summary" in text and "patterns" in text
    assert "evidence_ids" in text
    assert "anti_positioning" in text
    assert "profile-local" in text
    assert "ai-core" in text
