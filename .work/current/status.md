# Current Status

## Root question

如何在兩台電腦安全延續 Resume OS，同步程式與必要人物資料，又不讓真實履歷進入 Git？

## Blocker

- GitHub CLI token 無效；HTTPS push 無帳密，SSH 亦無可用 GitHub key。推送與 Release 上傳需先完成 `bluemaple18-home` GitHub 認證。
- 朋友真實 104 履歷尚未提供，Task 8 保持 `waiting_for_fixture`。

## Fork

- 程式與技術 handoff：Git repository。
- Matt 真實 profile 與訪談：加密 GitHub Release asset，不進 Git tree/history。

## 目前狀態

- Task 1–7 與 Task 8 synthetic acceptance 已完成。
- Matt profile 已建立能力模型、三個專案與履歷開頭摘要。
- 現職經歷有一份通過 Evidence Guard、尚待使用者核准的 bullets proposal。

## 下一步

1. 執行 `gh auth login -h github.com -p https -w` 完成 GitHub 認證。
2. 推送目前完整歷史到目標 repository。
3. 將已驗證的加密人物資料包上傳為 GitHub Release asset。

## 等待條件

- 有效 GitHub 認證。
- 朋友真實履歷 fixture。

## 限制

- 不得把 `profiles/`、真實來源、訪談原文、exports 或 API key 加入 Git。
- LLM 只產生訪談與文字候選；canonical mutation 走 deterministic CLI。
