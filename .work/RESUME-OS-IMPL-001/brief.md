# RESUME-OS-IMPL-001

任務ID：RESUME-OS-IMPL-001  
卡片類型｜派工對象：Implementation｜新 Codex thread  
請讀：`docs/superpowers/specs/2026-07-03-resume-os-codex-mvp-design.md`、`docs/superpowers/plans/2026-07-05-resume-os-codex-mvp-implementation.md`、`.work/RESUME-OS-IMPL-001/context_manifest.md`  
任務目的：依計畫執行 Task 1–8，先完成 deterministic core，再建立與驗證 repo-local Resume OS Skill。  
證據路徑：`.work/RESUME-OS-IMPL-001/evidence/`

## 執行要求

- 第一拍只讀上述文件與 repository 狀態，確認限制後再修改。
- 使用 Python `uv + .venv`，所有有行為價值的邏輯採 TDD。
- 人物資料必須隔離；真實 profile、履歷、API key 與輸出不得進 Git。
- LLM 只能提出問題與候選文字；profile、merge、conflict、Evidence Guard、approval、version、export 都由 deterministic code 執行。
- 每完成一個 Task，跑該 Task 驗證並提交；每個 checkpoint 跑完整受影響測試與 `git diff --check`。
- 未取得朋友真實履歷前，不得宣稱 Task 8 真實雙人物驗收完成。

## 完成條件

- Task 1–7 實作與自動測試通過。
- Task 8 synthetic acceptance 通過。
- Skill validation 通過。
- 本人真實履歷驗收完成；朋友履歷若尚未提供，狀態明確標成 `waiting_for_fixture`。
- `status.md`、`result.md` 與 `evidence/` 已更新。
