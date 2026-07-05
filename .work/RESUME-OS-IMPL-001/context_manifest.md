# Context Manifest

## 必读

- `docs/superpowers/specs/2026-07-03-resume-os-codex-mvp-design.md`
- `docs/superpowers/plans/2026-07-05-resume-os-codex-mvp-implementation.md`
- `.work/RESUME-OS-IMPL-001/brief.md`
- `AGENTS.md`（若 repository 中存在）

## 已確認產品決策

- 第一版在 Codex 運作，本機儲存；通過後才做本機網頁。
- 主要輸入為 104 履歷連結；失敗 fallback 為 PDF 或文字。
- 每位人物使用獨立資料庫，不共用履歷、回答、版本或推測。
- 同一工作／專案合併為 canonical entity；版本不是獨立事件。
- 新舊資訊衝突時先質問。
- 每項修改顯示修改前、修改後、修改理由，使用者可接受、拒絕或編輯。
- 使用者是 PM，程式多由 AI 對答協作完成；不得誤寫為本人手寫工程架構。
- 不使用虛構單一 ATS 分數，採五項分項評估。

## 外部來源邊界

- Resume Matcher：只 adapt 規則與測試觀念，不搬整套系統。
- OpenResume：只 reference parser／schema 觀念，不複製 AGPL 程式碼。
- 其他來源依設計文件第 8 節分類，不自行安裝或擴大 MVP。

## Git 基線

- Design commit：`bd954c1`
- Open-source map commit：`fdc0422`
- Implementation plan commit：`7539f12`
