# Resume OS Capability Synthesis 設計規格

日期：2026-07-05
狀態：待使用者審閱

## 1. 問題

現行 Resume OS 在匯入履歷後直接進入缺口訪談與文字提案，缺少跨經歷的核心能力合成。這會使 LLM 將職稱、工具與工作項目直接當成能力，忽略不同經歷中重複出現的行為模式與可遷移優勢。

Resume OS 必須先回答「這個人反覆如何處理問題、創造價值」，才能判斷履歷應如何取捨與改寫。

## 2. 目標

在任何履歷改寫前，建立並取得使用者核准的 `Capability Profile`：

- 從完整履歷中找出跨公司、職稱、產業與任務反覆出現的能力模式。
- 區分表面工作項目與底層可遷移能力。
- 每項能力連回來源證據，不以抽象稱讚代替事實。
- 記錄正確定位與不應誤寫的定位。
- Capability Profile 未核准前，不得開始履歷摘要、經歷或技能改寫。

## 3. 資料邊界

### 3.1 專案 Git

只保存通用方法、schema、Skill 編排規則與 synthetic tests。不得保存任何真實人物的履歷、Capability Profile 或證據內容。

### 3.2 本機 profile

每位人物的 Capability Profile 儲存在其獨立 SQLite profile，與履歷、訪談回答、evidence 與版本共用同一隔離邊界。`profiles/` 維持 Git ignored。

### 3.3 ai-core

本功能不讀寫 `ai-core`，不把人物能力模型當成全域記憶。

## 4. Capability Profile 模型

Capability Profile 是 profile 內的 canonical entity，至少包含：

- `summary`：一句整體能力定位。
- `patterns`：一至五項可遷移能力模式。
- `evidence_ids`：每項模式的來源證據。
- `positioning`：履歷應主打的角色與價值。
- `anti_positioning`：不應誤寫成的角色或所有權宣稱。

能力名稱是合成結果，不是履歷原文抽詞。每項能力原則上需由至少兩段不同經歷支持；若只有單一來源，必須標記為待確認，不得當成穩定核心能力。

## 5. 工作流

```text
匯入完整履歷與來源
        ↓
建立 canonical experiences / projects 候選
        ↓
跨經歷找重複行為模式
        ↓
產生 Capability Profile proposal
  ├─ 整體定位
  ├─ 核心能力
  ├─ 證據對應
  └─ 誤寫風險
        ↓
使用者接受、拒絕或編輯
        ↓
核准後才開始缺口訪談與履歷改寫
```

Skill 不得先從希望職稱、技能清單或單一工作項目推導整體定位。必須先讀完主要經歷，再做跨經歷合成。

## 6. LLM 與 deterministic core 邊界

LLM 可以：

- 找候選的重複行為模式。
- 產生能力名稱、整體定位與錯誤定位風險候選。
- 指出證據不足並提出訪談問題。

Deterministic core 必須：

- 只讀 active profile 的 evidence。
- 驗證所有 `evidence_ids` 存在且屬於當前 profile。
- 以 proposal lifecycle 處理接受、拒絕與編輯。
- 只將已核准的 Capability Profile 提供給後續改寫流程。
- 保存版本並維持人物隔離。

## 7. 錯誤與停止條件

- 履歷主要經歷尚未讀完：停止定位與訪談。
- 能力只有職稱、工具或單一任務支持：標記為不足，不寫入 canonical Capability Profile。
- 核心能力與人物現實貢獻衝突：建立問題，不自動採用。
- Capability Profile 未核准：禁止進入履歷改寫。

## 8. 驗收標準

1. Skill contract 明確要求讀完原始履歷後才進行核心能力合成。
2. Skill 禁止將職稱、工具或工作項目的字面意義直接當成核心能力。
3. Capability Profile 是獨立 canonical entity，且每位人物完全隔離。
4. 每項穩定核心能力可追溯至至少兩段經歷 evidence。
5. Capability Profile 未核准時，Skill 不得產生履歷改寫提案。
6. Capability Profile 的修改使用現有的修改前、修改後、修改理由、Evidence Guard 與核准流程。
7. Matt 的真實 Capability Profile 只存在本機 ignored profile，Git 不含其內容。

## 9. 非目標

- 不建立通用能力分類學或能力分數。
- 不將人物 Capability Profile 寫入 `ai-core`。
- 不因為能力合成而擴大至網頁、JD 匹配、LinkedIn 或英文履歷。
- 不讓 Capability Profile 取代事實證據、人工核准或原始履歷。
