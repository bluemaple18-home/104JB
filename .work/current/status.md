# Current Status

## Root question

如何在兩台電腦安全延續 Resume OS，同步程式與必要人物資料，又不讓真實履歷進入 Git？

## Blocker

- 朋友真實 104 履歷尚未提供，Task 8 保持 `waiting_for_fixture`。

## Fork

- 程式與技術 handoff：Git repository。
- Matt 真實 profile 與訪談：加密 GitHub Release asset，不進 Git tree/history。

## 目前狀態

- Task 1–7 與 Task 8 synthetic acceptance 已完成。
- Matt profile 已建立能力模型、三個專案與履歷開頭摘要。
- 現職經歷有一份通過 Evidence Guard、尚待使用者核准的 bullets proposal。
- 程式已推送至 `bluemaple18-home/104JB` 的 `main`。
- 私有人物資料已加密並上傳至 Release `handoff-20260706`，密碼未存於 GitHub。

## 下一步

1. 另一台電腦 clone repository 並閱讀 `.work/current/handoff.md`。
2. 下載、驗證、解密 Release asset，再還原 ignored 私人資料。
3. 另一台建立獨立 branch 或 worktree 後再開始平行開發。

## 等待條件

- 朋友真實履歷 fixture。

## 限制

- 不得把 `profiles/`、真實來源、訪談原文、exports 或 API key 加入 Git。
- LLM 只產生訪談與文字候選；canonical mutation 走 deterministic CLI。
