# Resume OS Capability Synthesis Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在履歷改寫前建立第一級 Capability Profile，要求跨經歷合成核心能力、追溯證據並取得使用者核准。

**Architecture:** 新增 `capability` canonical entity kind，沿用每人物獨立 SQLite、evidence、proposal approval 與 version history。Repo-local Skill 在來源匯入後先讀完主要經歷、合成 Capability Profile 並等待核准；核准前不得進入履歷文案改寫。

**Tech Stack:** Python 3.12+、uv、SQLite、Pydantic v2、pytest、Codex Agent Skill

---

## File Map

| Path | Responsibility |
|---|---|
| `src/resume_os/models.py` | 新增 `EntityKind.CAPABILITY` |
| `tests/test_database.py` | 驗證 Capability Profile 可儲存且 profile 隔離 |
| `tests/test_export_104.py` | 驗證內部 Capability Profile 不會變成 104 空段落 |
| `.codex/skills/resume-os/SKILL.md` | 新增改寫前的 Capability Synthesis 強制門 |
| `.codex/skills/resume-os/references/workflow.md` | 說明 Capability Profile artifact 與 approval contract |
| `tests/test_skill_contract.py` | 固定讀完原履歷、跨經歷合成與核准前禁止改寫 |

## Task 1：Capability canonical entity

**Files:**
- Modify: `src/resume_os/models.py`
- Modify: `tests/test_database.py`
- Modify: `tests/test_export_104.py`

- [ ] **Step 1: 建立失敗測試**

```python
def test_capability_profile_is_a_profile_scoped_canonical_entity(tmp_path: Path) -> None:
    matt = ResumeDatabase(tmp_path / "matt" / "resume.sqlite")
    friend = ResumeDatabase(tmp_path / "friend" / "resume.sqlite")
    entity_id = matt.create_entity(
        EntityKind.CAPABILITY,
        "capability:core",
        {"name": "Synthetic Capability Profile", "summary": "Cross-domain integration"},
    )

    assert matt.get_entity(entity_id)["summary"] == "Cross-domain integration"
    with pytest.raises(KeyError):
        friend.get_entity(entity_id)


def test_render_104_does_not_emit_internal_capability_section() -> None:
    output = render_104([
        {"kind": "capability", "name": "Synthetic Capability Profile"},
        {"kind": "project", "name": "Synthetic Project"},
    ])

    assert "Synthetic Capability Profile" not in output
    assert "Synthetic Project" in output
```

- [ ] **Step 2: 執行 RED**

Run: `uv run pytest tests/test_database.py tests/test_export_104.py -q`
Expected: FAIL，`EntityKind` 沒有 `CAPABILITY`。

- [ ] **Step 3: 最小實作**

```python
class EntityKind(StrEnum):
    BASICS = "basics"
    EXPERIENCE = "experience"
    PROJECT = "project"
    EDUCATION = "education"
    SKILL = "skill"
    CAPABILITY = "capability"
```

Exporter 維持現有 section allowlist，不新增 `capability` section。

- [ ] **Step 4: 執行 GREEN**

Run: `uv run pytest tests/test_database.py tests/test_export_104.py -q`
Expected: PASS。

- [ ] **Step 5: 驗證與提交**

Run: `git diff --check`
Expected: 無輸出。

```bash
git add src/resume_os/models.py tests/test_database.py tests/test_export_104.py
git commit -m "feat: add capability profile entity"
```

## Task 2：Skill Capability Synthesis contract

**Files:**
- Modify: `tests/test_skill_contract.py`
- Modify: `.codex/skills/resume-os/SKILL.md`

- [ ] **Step 1: 建立 Skill contract RED**

```python
def test_skill_synthesizes_capabilities_before_resume_rewriting() -> None:
    text = Path(".codex/skills/resume-os/SKILL.md").read_text("utf-8")
    assert "讀完整份原始履歷" in text
    assert "Capability Profile" in text
    assert "至少兩段不同經歷" in text
    assert "不得只從職稱、工具或單一工作項目" in text
    assert "Capability Profile 未核准前，不得開始履歷改寫" in text
```

- [ ] **Step 2: 執行 RED**

Run: `uv run pytest tests/test_skill_contract.py -q`
Expected: FAIL，現有 Skill 沒有 Capability Synthesis contract。

- [ ] **Step 3: 寫入最小 Skill gate**

在 `## Workflow` 的來源匯入後、缺口訪談前加入：

```markdown
4. 讀完整份原始履歷的主要經歷，再開始定位。
5. 跨公司、職稱、產業與任務合成 Capability Profile。每項穩定核心能力需由至少兩段不同經歷支持。
6. 不得只從職稱、工具或單一工作項目推導核心能力。
7. 顯示 Capability Profile 的整體定位、能力模式、證據對應與誤寫風險，讓使用者接受、拒絕或編輯。
8. Capability Profile 未核准前，不得開始履歷改寫。
```

後續步驟重新編號，不改變 profile、Evidence Guard 與 approval 邊界。

- [ ] **Step 4: 執行 GREEN 與 validator**

Run: `uv run pytest tests/test_skill_contract.py -q`
Expected: PASS。

Run: `python3 "$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py" .codex/skills/resume-os`
Expected: `Skill is valid!`

- [ ] **Step 5: 驗證與提交**

Run: `git diff --check`
Expected: 無輸出。

```bash
git add .codex/skills/resume-os/SKILL.md tests/test_skill_contract.py
git commit -m "feat: require capability synthesis before rewriting"
```

## Task 3：Capability artifact contract

**Files:**
- Modify: `.codex/skills/resume-os/references/workflow.md`
- Modify: `tests/test_skill_contract.py`

- [ ] **Step 1: 建立 artifact contract RED**

```python
def test_capability_workflow_requires_evidence_and_profile_local_storage() -> None:
    text = Path(".codex/skills/resume-os/references/workflow.md").read_text("utf-8")
    assert "capability:core" in text
    assert "summary" in text and "patterns" in text
    assert "evidence_ids" in text
    assert "anti_positioning" in text
    assert "profile-local" in text
    assert "ai-core" in text
```

- [ ] **Step 2: 執行 RED**

Run: `uv run pytest tests/test_skill_contract.py -q`
Expected: FAIL，workflow reference 尚未定義 artifact contract。

- [ ] **Step 3: 加入最小 reference**

```markdown
## Capability Profile gate

Create one `capability:core` entity in the active profile. Keep `summary`, `patterns`, `evidence_ids`, `positioning`, and `anti_positioning` profile-local. Never write person-specific capability content to Git or ai-core.

Each stable pattern must cite evidence from at least two different experiences. Create capability changes through proposal create/edit/accept; do not continue to resume rewriting until the Capability Profile is accepted.
```

- [ ] **Step 4: 執行 GREEN**

Run: `uv run pytest tests/test_skill_contract.py -q`
Expected: PASS。

- [ ] **Step 5: 驗證與提交**

Run: `git diff --check`
Expected: 無輸出。

```bash
git add .codex/skills/resume-os/references/workflow.md tests/test_skill_contract.py
git commit -m "docs: define capability profile artifact contract"
```

## Task 4：全量驗證與本機 Matt Capability Profile

**Files:**
- Git tracked files: 無新增真實人物資料
- Local runtime: `profiles/matt/resume.sqlite` (Git ignored)

- [ ] **Step 1: 執行全量驗證**

Run: `uv run pytest -q`
Expected: 全部 PASS。

Run: `python3 "$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py" .codex/skills/resume-os`
Expected: `Skill is valid!`

Run: `git diff --check && git status --short`
Expected: diff check 無輸出；`profiles/` 與 `.resume-os/` 不出現在 Git status。

- [ ] **Step 2: 建立本機 Capability Profile 草案**

在 active `matt` profile 中建立 `capability:core` entity。只使用已匯入的 104 來源與本次訪談 evidence，將合成結果建立為 pending proposal；不自動 accept。

- [ ] **Step 3: 驗證人物資料未進 Git**

Run: `git status --short --untracked-files=all`
Expected: 不顯示 `profiles/matt/`、`.resume-os/` 或真實履歷來源。

- [ ] **Step 4: 呈現 pending Capability Profile**

回報修改前、修改後、修改理由、evidence 與 Evidence Guard 狀態，等待使用者接受、拒絕或編輯。

## Plan Self-Review

- Spec coverage：first-class capability entity、跨經歷合成、核准前停止改寫、profile isolation、Git/ai-core 邊界均有對應 Task。
- Scope：不建立能力分數或 ontology；不擴大至 JD、網頁或英文履歷。
- Type consistency：統一使用 `EntityKind.CAPABILITY`、`capability:core`、`Capability Profile`。
- Privacy：真實 Capability Profile 只寫入 ignored SQLite，計畫與測試只用 synthetic content。
