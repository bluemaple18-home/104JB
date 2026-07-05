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
