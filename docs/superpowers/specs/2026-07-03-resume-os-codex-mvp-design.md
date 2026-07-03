# Resume OS：Codex MVP 設計規格

日期：2026-07-03
狀態：待使用者最終審閱

## 1. 問題與目標

### 1.1 問題

目標使用者是產品本人，以及把 104 履歷交給產品本人協助修改的朋友。現有履歷可能能被人閱讀，但未必能被 ATS 或 AI 篩選系統正確解析，也常缺少清楚的角色定位、本人貢獻、成果證據與必要脈絡。

單純使用 LLM 改寫有三個主要風險：

- 資訊不足時自行補故事、數字或技能。
- 看見 GitHub 程式碼後，把 PM 誤寫成工程師。
- 每次修改都產生新的孤立版本，無法累積成可信的 Master Resume。

### 1.2 MVP 目標

建立一套在 Codex 內運作的本機履歷工作流。使用者提供 104 履歷連結後，系統解析原履歷、找出缺口、進行訪談、提出可核准的修改建議，最後形成可持續更新的繁中 104 Master Resume。

第一階段成功不以虛構的單一 ATS 分數衡量，而以履歷的可解析性、角色清晰度、成果證據、技能完整性與可信度進行分項評估。

## 2. 使用者與範圍

### 2.1 目標使用者

- 主要使用者：產品本人。
- 次要使用者：由產品本人協助修改履歷的朋友。
- 每位人物的資料必須完全隔離，不得共用履歷、回答、版本或推測結果。

### 2.2 MVP 範圍

- 在 Codex 中完成完整工作流。
- 主要輸入為 104 履歷連結。
- 連結無法讀取時，支援 PDF 上傳或文字貼上。
- 只處理繁體中文 104 履歷。
- 產出修改前、修改後、修改理由及核准狀態。
- 保存每位人物自己的 Master Resume、訪談記憶、版本與來源證據。
- 產出可由使用者自行貼回 104 的完整內容。

### 2.3 非 MVP 範圍

- 不自動登入或修改 104。
- 不先做 LinkedIn、CakeResume、英文履歷或 Cover Letter。
- 不先做公開 SaaS、雲端帳號或跨裝置同步。
- 不先做本機網頁；Codex 流程驗證成功後再規劃。
- 不宣稱能模擬所有企業 ATS，也不產生無依據的通用 ATS 總分。

## 3. 核心產品原則

1. **使用者最終決定**：AI 只提出建議，未核准內容不得寫入 Master Resume。
2. **不得虛構**：公司、職稱、日期、數字、成果、技能、證照與本人貢獻都必須有來源。
3. **資訊不足就問**：關鍵問題逐題追問；日期、工具等簡單資料可集中詢問。
4. **衝突先質問**：新舊資訊不一致時，先列出差異並取得答案，不自動覆蓋。
5. **同一事件只留一份**：新資訊合併至既有工作、專案或成果；版本歷史不得變成重複履歷事件。
6. **區分 PM 與 AI 貢獻**：使用者可負責問題定義、需求、規則、判斷與驗收，程式實作則由 AI 協助；系統不得把後者誤寫成使用者的工程能力。
7. **人物完全隔離**：共用的只有方法、規則與模板，任何人物內容不得跨 profile 流動。

## 4. 核心流程

```text
建立或選擇人物 profile
        ↓
貼上 104 履歷連結
        ↓
嘗試讀取內容
  ├─ 成功：解析履歷
  └─ 失敗：PDF 上傳或文字貼上
        ↓
建立或比對該人物的 Master Resume
        ↓
檢查重複、缺口、弱敘述與資料矛盾
        ↓
關鍵問題逐題訪談；簡單資料集中詢問
        ↓
產生修改提案
  ├─ 修改前
  ├─ 修改後
  └─ 修改理由與證據
        ↓
使用者逐項接受、拒絕或自行編輯
        ↓
只把核准內容合併回 Master Resume
        ↓
輸出可貼回 104 的完整履歷
        ↓
產出五項 AI／ATS 友善度評估
```

## 5. 元件邊界

### 5.1 Codex Skill

負責啟動流程、選擇人物、協調解析、依缺口提問、展示修改提案及執行核准操作。Skill 不直接把模型輸出視為可信事實。

### 5.2 Profile Store

每位人物使用獨立 SQLite 檔案。Profile Store 只允許在明確選定 active profile 後讀寫。

```text
profiles/
├── matt/
│   ├── resume.sqlite
│   ├── sources/
│   └── exports/
└── friend_a/
    ├── resume.sqlite
    ├── sources/
    └── exports/

shared/
├── review_rules/
└── output_templates/
```

### 5.3 Resume Parser

把 104 頁面、PDF 或文字轉成候選結構。解析結果若不確定，必須保留原文並要求使用者確認。

### 5.4 Interview Engine

根據缺少的事實決定下一個問題。優先詢問：本人角色、問題背景、實際行動、成果、規模、使用者、時間與可驗證數字。不得為了湊滿欄位而提出無價值問題。

### 5.5 Proposal／Diff Engine

每項修改提案保存原文、建議文字、理由、使用的證據與狀態。狀態只能是：`pending`、`accepted`、`rejected`、`edited`。

### 5.6 Evidence Guard

檢查建議中新增的數字、技能、證照、公司、職稱、日期、成果與所有權宣稱。找不到支持來源時，提案不得進入可核准狀態。

### 5.7 104 Exporter

把核准後的 Master Resume 整理成可貼回 104 的繁中欄位內容。MVP 只輸出，不操作 104 帳號。

## 6. 每位人物的資料模型

### 6.1 Master Resume

保存基本資料、求職方向、工作經歷、專案、技能與學歷。工作或專案需要穩定識別資料，避免每輪訪談產生重複事件。

### 6.2 Evidence

每項事實記錄來源，例如：

- 104 原文。
- 使用者訪談回答。
- 使用者確認過的 GitHub repo 或文件。
- 已核准的舊版本。

證據需能表達本人貢獻類型，例如 `owner_decision`、`business_rule`、`validation`、`ai_assisted_implementation`，避免把 AI 產生的程式碼等同本人手寫。

### 6.3 Change Proposal

至少包含：目標欄位、修改前、修改後、修改理由、證據引用、風險旗標及狀態。

### 6.4 Version History

保存核准前後的變更與時間，以便追蹤和還原。版本是 canonical entity 的歷史，不是新的工作或專案事件。

### 6.5 Conflict Question

當同一事實出現不同日期、數字、角色或結果時建立。衝突未解決前，不得更新 canonical 值。

## 7. 共用規則

共用規則只描述處理方法，不含人物資料：

- 104／PDF／文字解析規則。
- AI／ATS 友善度檢查規則。
- 訪談問題排序與停止條件。
- 真實性與本人貢獻判定規則。
- canonical 合併與去重規則。
- 衝突質問規則。
- 修改比對與核准規則。
- 104 欄位輸出規則。

## 8. 開源專案與技術來源地圖

本專案不會把外部 repository 整包拼接成產品。每個來源都先分類為 `adapt`、`reference`、`defer`、`needs_review` 或 `reject`，並記錄進入 MVP 的邊界。

| 來源 | 分類 | Codex MVP 用途 | 後續用途與邊界 |
|---|---|---|---|
| [OpenResume](https://github.com/xitanggg/open-resume) | `reference` | 參考 PDF 版面解析、履歷基本欄位與 ATS-friendly 排版觀念 | Parser 偏英文 section keyword，Schema 沒有證據、人物隔離與版本；採 AGPL-3.0，MVP 不複製其程式碼 |
| [Resume Matcher](https://github.com/srbhr/Resume-Matcher) | `adapt` | 參考逐題訪談、Master Resume、區段更新、Diff、弱敘述追問與防虛構規則 | 採 Apache-2.0；只改寫需要的規則與測試，不搬入整套前後端 |
| [Resume Tailor](https://github.com/farmerTheodor/Resume-Tailor) | `needs_review` | 不作依賴 | 目前無法可靠查證 repository 內容與授權；找到正確來源前不得引用或安裝 |
| OpenAI Resume forks | `needs_review` | 不使用未指名來源的 Prompt | 必須先取得確切 repository、commit 與 license，才能評估 Achievement Rewrite 或 Cover Letter 規則 |
| [RateIn](https://github.com/alessandroamenta/RateIn) | `defer` | 不進 104 MVP | 可參考 LinkedIn profile 評估維度；其舊版 Assistants API、Vision 與 scraping 流程不可直接沿用 |
| LinkedIn MCP server | `needs_review` | 不進 104 MVP | 進入 LinkedIn 階段前，需確認確切 repo、OAuth 權限、平台條款、資料範圍與唯讀邊界 |
| [spaCy](https://github.com/explosion/spaCy) | `defer` | MVP 不需要額外 NLP runtime | 未來可做技能、公司、職稱與時間等 NER；採用前需用繁中 104 樣本驗證模型表現，不能假設英文模型適用 |
| [Sentence Transformers](https://github.com/huggingface/sentence-transformers) | `defer` | MVP 不做 JD 語意比對 | 未來用於技能同義詞與 Resume／JD 語意相似度；必須選擇支援繁中的模型並建立本地評估集 |
| [python-docx](https://github.com/python-openxml/python-docx) | `defer` | MVP 先輸出可貼回 104 的文字 | 後續 DOCX 匯出候選；採 MIT，可依核准後的 Master Resume 產生文件 |
| [ReportLab](https://docs.reportlab.com/) | `defer` | MVP 不產 PDF | 後續 PDF 匯出候選；需額外驗證繁中文字型、換頁與 ATS 文字層，不因能產 PDF 就視為 ATS-friendly |
| 既有三組模型 API | `defer` | Codex MVP 直接使用目前對話模型，不另接 API | 本機網頁階段才建立 provider adapter；API key 只從既有共用金鑰機制解析，不寫入 repo 或 profile database |

### 8.1 Resume Matcher 可吸收規則

採用其概念：

- 一次詢問一個關鍵問題。
- 不得虛構公司、職稱、日期、數字、技能、證照與成果。
- 只更新目前訪談區段，不讓模型覆蓋其他既有資料。
- 同一工作、學歷或專案依穩定識別資料合併。
- 保存問題、回答與修改前快照。
- 優先追問成果、規模、工具與本人貢獻。
- 把新增技能或證照視為高風險變更。
- 移除過度 AI 化的誇張詞與空泛企業黑話。

必須自行補強：

- 每位人物獨立資料庫。
- 104 繁中欄位規則。
- 新舊資訊衝突質問。
- PM 決策與 AI 實作的貢獻區分。
- 逐項修改理由與使用者核准。
- 可追溯 Evidence Guard。Resume Matcher 的測試已指出部分虛構敘事仍可能只能靠 Prompt 阻擋，因此本專案不能只依賴 Prompt。

### 8.2 OpenResume 可參考邊界

OpenResume 的欄位模型可作 Parser 的最小參考，但不能直接成為 canonical schema。Resume OS 還需要 profile ownership、來源證據、本人貢獻類型、衝突問題、提案狀態與版本歷史。

### 8.3 分階段啟用順序

1. Codex MVP：Resume Matcher 規則觀念、自建 profile database、Evidence Guard、104 文字輸出。
2. 104 MVP 驗證後：評估 python-docx 與 ReportLab，加入 DOCX／PDF 匯出。
3. 加入 JD 後：評估繁中 spaCy pipeline 與 Sentence Transformers 模型。
4. LinkedIn 階段：重新審核 RateIn 與具名 LinkedIn MCP，不沿用舊 scraping 或未確認權限。

## 9. 錯誤與安全邊界

- 104 連結無法讀取時，切換 PDF 或文字輸入。
- 欄位解析不確定時，保留原文並詢問。
- 未選 active profile 時，禁止讀寫。
- 嘗試跨 profile 讀取時，拒絕操作並停止該次流程。
- AI 新增無證據內容時，Evidence Guard 阻擋提案。
- 新舊資料衝突時，建立問題並保留原資料。
- 寫入失敗時，不破壞上一版 Master Resume，修改提案保持待處理。
- 使用者拒絕的內容不進正式履歷，但保留拒絕紀錄。
- API key 不寫入 repository 或 profile database；後續需要模型 API 時，沿用既有共用金鑰解析機制。

## 10. AI／ATS 友善度評估

MVP 只提供分項判斷與理由：

1. 可解析性：欄位、時間、標題與段落是否容易辨識。
2. 角色清晰度：目標職位與本人責任是否明確。
3. 成果證據：是否交代問題、行動、規模與結果。
4. 技能完整性：技能是否有實際經歷支持，且沒有無來源新增。
5. 可信度：數字、角色及成果是否可追溯至證據。

評估不得宣稱是所有企業 ATS 的統一分數。

## 11. MVP 驗收標準

1. 可建立兩個 profile，且資料完全隔離。
2. 可讀取 104 履歷；無法讀取時可使用 PDF 或文字。
3. 可由舊履歷建立 Master Resume。
4. 新回答會合併至同一工作或專案，不新增重複事件。
5. 新舊資訊衝突時會先質問。
6. 能區分本人貢獻與 AI 協助，不把 PM 誤寫成工程師。
7. 每項修改顯示修改前、修改後、理由與來源。
8. 使用者可逐項接受、拒絕或自行編輯。
9. 無來源技能、數字或成果會被阻擋。
10. 重開 Codex 後，可從該人物上次狀態接續。
11. 可輸出可貼回 104 的繁中履歷。
12. 可產出五項 AI／ATS 友善度評估及理由。

驗收必須完成兩個真實案例：

- 產品本人的履歷，包含 GitHub 作品與 AI 協作角色辨識。
- 一位朋友的 104 履歷，證明流程不只適用於單一人物。

## 12. 後續階段

Codex MVP 通過兩個案例後，才設計本機網頁。網頁沿用相同 Profile Store、Interview Engine、Proposal／Diff Engine 與 Evidence Guard，不重做第二套履歷規則。
