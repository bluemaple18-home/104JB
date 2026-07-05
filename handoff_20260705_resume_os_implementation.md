# Resume OS Implementation Handoff

## Root Question

如何依已核准規格，完成一套人物資料隔離、證據約束、使用者逐項核准的 Codex 履歷修改 MVP？

## Goal

由新的 Codex 實作 thread 依 `docs/superpowers/plans/2026-07-05-resume-os-codex-mvp-implementation.md` 執行 Task 1–8；本 thread 保留為產品決策與驗收主線。

## Constraints & Preferences

- 預設繁體中文；程式註解與 docstring 使用繁中。
- Python 使用 `uv + .venv`。
- 新 thread 使用獨立 worktree。
- 先 TDD、再最小實作、再驗證與提交。
- 真實人物資料、履歷、API key、profiles 與 exports 不得進 Git。
- 不得把 AI 協助實作寫成使用者本人具備工程實作能力。
- 不得自動修改 104；輸出交由使用者自行評估與貼回。

## Completed Actions

- 完成產品啟動訪談與角色釐清。
- 盤點 `bluemaple18-home` 公開作品，確認 MDreport2、IAS-Dashboard、NEW-TOP10 的本人貢獻邊界。
- 完成並提交設計：`docs/superpowers/specs/2026-07-03-resume-os-codex-mvp-design.md`。
- 補齊開源專案與技術來源地圖。
- 完成並提交八切片實作計畫：`docs/superpowers/plans/2026-07-05-resume-os-codex-mvp-implementation.md`。
- 建立實作卡：`.work/RESUME-OS-IMPL-001/brief.md`。

## Active State

- Repository 主線只有文件與派工資料，尚無產品程式碼。
- 本 thread 不執行 Task 1–8，等待新 thread 接手。
- 沒有啟動 server 或背景程序。

## In Progress / Remaining Work

- 新 thread 從 Task 1 人物隔離開始。
- 依計畫完成 deterministic core、CLI、Codex Skill 與 synthetic acceptance。
- 最後使用產品本人與一位朋友的真實履歷驗收。

## Blocker

目前無實作 blocker。

## Candidate Fork

Codex MVP 通過後，另開本機網頁設計與實作卡；不得在本卡提前加入網頁。

## Waiting Conditions

- Task 8 朋友真實履歷驗收需使用者提供一份 104 履歷。
- 若未提供，只能標記 `waiting_for_fixture`，不得宣稱 MVP 完全驗收。

## Limits

- 不擴大到 LinkedIn、CakeResume、英文履歷、Cover Letter、公開 SaaS 或雲端同步。
- 不直接複製 OpenResume AGPL 程式碼。
- 不自行安裝未審核的 LinkedIn MCP、Resume Tailor 或其他外部 runtime。

## Next Step

讀取 `.work/RESUME-OS-IMPL-001/brief.md` 與 context manifest，確認 repository clean，執行 Task 1 的 failing tests。
