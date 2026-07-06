# Resume OS 多機 Handoff

## Goal

讓另一台電腦可直接接續 Resume OS MVP 開發與 Matt 履歷整理。

## Constraints & Preferences

- 預設繁體中文。
- Python 使用 `uv + .venv`。
- 兩台同時開發必須分 branch 或 worktree。
- 真實人物資料不得進 Git；只可由加密交接資產還原到 ignored 路徑。
- Task 8 在朋友真實履歷提供前保持 `waiting_for_fixture`。

## Completed Actions

- Task 1–7 與 Task 8 synthetic acceptance 已完成並提交。
- Capability Profile gate、Evidence Guard 與 AI-assisted contribution boundary 已完成。
- Matt profile 已保存於本機 ignored `profiles/matt/`。
- 本機訪談紀錄保存於 ignored `.work/RESUME-OS-IMPL-001/interview_record.md`。

## Active State

- 主力 branch：`codex/resume-os-mvp`。
- 目前無 server。
- tracked working tree 在建立本 handoff 前為乾淨狀態。
- 私有人物資料會封裝為加密 Release asset；不會出現在 Git diff。

## In Progress / Remaining Work

- 現職經歷 bullets proposal 已通過 Evidence Guard，仍待使用者接受、拒絕或編輯。
- 其餘歷史工作經歷尚待依相同流程逐段整理。
- 朋友真實履歷到位後，需建立另一個獨立 profile 完成真實雙人物驗收。

## Blocked & Errors

- `gh auth status` 顯示本機 GitHub token 無效；外部推送前需重新登入。
- 沒有朋友真實 104 fixture，不能宣稱完整 MVP 驗收完成。

## Key Decisions & Resolved Questions

- 使用者定位為跨域整合型數位專案經理，AI/Vibe Coding 是附加能力。
- 程式由 AI 協作不等於使用者本人手寫工程架構。
- Matt 人物資料採加密 Release asset 搬移，避免公開 repository 洩漏個資。

## Changed files

- `.work/current/brief.md`
- `.work/current/status.md`
- `.work/current/handoff.md`
- `.work/current/context_manifest.md`
- `.work/current/result.md`

## Do not touch

- `profiles/`、`exports/` 與 ignored 訪談紀錄不得解除忽略或加入 Git。
- 不得在未取得朋友 fixture 前改寫 Task 8 狀態為 complete。

## Verification

- 接手前執行 `git status --short`、`git worktree list`。
- 執行 `uv run pytest` 與 `git diff --check`。
