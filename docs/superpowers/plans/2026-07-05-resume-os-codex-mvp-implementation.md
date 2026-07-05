# Resume OS Codex MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立一套本機優先、人物資料隔離、證據約束且由使用者逐項核准的 Codex 履歷修改工作流。

**Architecture:** Python 套件提供 deterministic core：每位人物一個 SQLite、來源匯入、canonical merge、conflict、Evidence Guard、proposal approval、104 exporter。Codex Skill 只負責訪談與編排，所有資料寫入與安全閘門都呼叫 CLI，不讓 Prompt 直接改資料庫。

**Tech Stack:** Python 3.12、uv、SQLite、Pydantic v2、httpx、BeautifulSoup、pypdf、pytest、Codex Agent Skill

---

## Scope 與依賴順序

```text
Slice 1 Profile isolation
  ↓
Slice 2 Canonical store + versioning
  ↓
Slice 3 Source ingestion
  ↓
Slice 4 Merge + conflict questions
  ↓
Slice 5 Evidence Guard + proposals + approval
  ↓
Slice 6 104 export + five-part evaluation
  ↓
Slice 7 Codex Skill orchestration
  ↓
Slice 8 Two-profile acceptance
```

## File Map

| Path | Responsibility |
|---|---|
| `pyproject.toml` | Python、dependencies、`resume-os` CLI entrypoint、pytest config |
| `.gitignore` | 排除真實 profiles、active profile 與本機輸出 |
| `src/resume_os/models.py` | Canonical entity、evidence、conflict、proposal schemas |
| `src/resume_os/profiles.py` | profile 建立、列出、選擇與 path traversal 防護 |
| `src/resume_os/database.py` | 每 profile SQLite schema、transaction、version snapshots |
| `src/resume_os/sources.py` | 104 URL、HTML、PDF、文字來源匯入與 fallback 狀態 |
| `src/resume_os/merge.py` | stable key、同事件合併、衝突偵測 |
| `src/resume_os/evidence.py` | 支持來源比對與 Evidence Guard |
| `src/resume_os/proposals.py` | 修改提案、接受、拒絕、自編輯 |
| `src/resume_os/evaluation.py` | 五項 AI／ATS 友善度 deterministic rubric |
| `src/resume_os/export_104.py` | 繁中 104 欄位輸出 |
| `src/resume_os/cli.py` | Codex 與使用者共用 CLI |
| `.codex/skills/resume-os/SKILL.md` | 訪談與安全編排規則 |
| `.codex/skills/resume-os/agents/openai.yaml` | Codex Skill UI metadata |
| `.codex/skills/resume-os/references/workflow.md` | CLI 指令與 artifact contract |
| `tests/` | 對 public behavior 的 pytest suites |
| `tests/fixtures/` | 無個資的 104 HTML／文字與兩個 synthetic profiles |

## Task 1：專案骨架與人物隔離

**Dependencies:** 無
**Acceptance:** 可建立、列出及選擇人物；非法 slug、未選人物與跨人物 path 都 fail loud。
**Gate:** `schema_gate`；CLI exit code 非零即停止。

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `src/resume_os/__init__.py`
- Create: `src/resume_os/profiles.py`
- Create: `src/resume_os/cli.py`
- Test: `tests/test_profiles.py`

- [ ] **Step 1: 建立失敗測試**

```python
# tests/test_profiles.py
from pathlib import Path

import pytest

from resume_os.profiles import NoActiveProfile, ProfileManager


def test_profiles_are_separate_and_require_explicit_selection(tmp_path: Path) -> None:
    manager = ProfileManager(tmp_path)
    matt = manager.create("matt", "Matt")
    friend = manager.create("friend-a", "Friend A")

    assert matt.database_path != friend.database_path
    with pytest.raises(NoActiveProfile):
        manager.active()

    manager.select("matt")
    assert manager.active().slug == "matt"
    assert manager.active().database_path.parent.name == "matt"


@pytest.mark.parametrize("slug", ["../friend", "Matt", "a/b", "", "."])
def test_profile_slug_rejects_path_traversal(tmp_path: Path, slug: str) -> None:
    manager = ProfileManager(tmp_path)
    with pytest.raises(ValueError):
        manager.create(slug, "Invalid")
```

- [ ] **Step 2: 執行 RED**

Run: `uv run pytest tests/test_profiles.py -q`
Expected: FAIL，`ModuleNotFoundError: No module named 'resume_os'`。

- [ ] **Step 3: 建立最小 package 與 profile manager**

```toml
# pyproject.toml
[project]
name = "resume-os"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
  "beautifulsoup4>=4.13,<5",
  "httpx>=0.28,<1",
  "pydantic>=2.12,<3",
  "pypdf>=5,<7",
]

[project.scripts]
resume-os = "resume_os.cli:main"

[dependency-groups]
dev = ["pytest>=8.4,<9"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

```gitignore
# .gitignore
.venv/
__pycache__/
.pytest_cache/
.resume-os/
profiles/
exports/
```

```python
# src/resume_os/profiles.py
import json
import re
from dataclasses import dataclass
from pathlib import Path

SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class NoActiveProfile(RuntimeError):
    pass


@dataclass(frozen=True)
class Profile:
    slug: str
    display_name: str
    root: Path

    @property
    def database_path(self) -> Path:
        return self.root / "resume.sqlite"


class ProfileManager:
    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace.resolve()
        self.profiles_root = self.workspace / "profiles"
        self.state_path = self.workspace / ".resume-os" / "active-profile.json"

    def create(self, slug: str, display_name: str) -> Profile:
        if not SLUG.fullmatch(slug):
            raise ValueError("profile slug must use lowercase letters, digits, and hyphens")
        root = (self.profiles_root / slug).resolve()
        if root.parent != self.profiles_root.resolve():
            raise ValueError("profile path escapes profiles root")
        root.mkdir(parents=True, exist_ok=False)
        (root / "sources").mkdir()
        (root / "exports").mkdir()
        (root / "profile.json").write_text(
            json.dumps({"slug": slug, "display_name": display_name}, ensure_ascii=False),
            encoding="utf-8",
        )
        return Profile(slug, display_name, root)

    def get(self, slug: str) -> Profile:
        payload = json.loads((self.profiles_root / slug / "profile.json").read_text("utf-8"))
        return Profile(payload["slug"], payload["display_name"], self.profiles_root / slug)

    def list(self) -> list[Profile]:
        if not self.profiles_root.exists():
            return []
        return [self.get(path.name) for path in sorted(self.profiles_root.iterdir()) if path.is_dir()]

    def select(self, slug: str) -> Profile:
        profile = self.get(slug)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps({"slug": slug}), encoding="utf-8")
        return profile

    def active(self) -> Profile:
        if not self.state_path.exists():
            raise NoActiveProfile("select a profile before reading or writing resume data")
        return self.get(json.loads(self.state_path.read_text("utf-8"))["slug"])
```

- [ ] **Step 4: 實作 argparse CLI 的 `profile create|list|select`，所有命令從 `Path.cwd()` 建立 `ProfileManager`**

```python
# src/resume_os/cli.py
import argparse
from pathlib import Path

from resume_os.profiles import ProfileManager


def main() -> None:
    parser = argparse.ArgumentParser(prog="resume-os")
    sub = parser.add_subparsers(dest="command", required=True)
    profile = sub.add_parser("profile")
    actions = profile.add_subparsers(dest="action", required=True)
    create = actions.add_parser("create")
    create.add_argument("slug")
    create.add_argument("--display-name", required=True)
    actions.add_parser("list")
    select = actions.add_parser("select")
    select.add_argument("slug")
    args = parser.parse_args()
    manager = ProfileManager(Path.cwd())
    if args.action == "create":
        print(manager.create(args.slug, args.display_name).slug)
    elif args.action == "select":
        print(manager.select(args.slug).slug)
    else:
        for item in manager.list():
            print(f"{item.slug}\t{item.display_name}")
```

- [ ] **Step 5: 執行 GREEN 與 smoke**

Run: `uv sync && uv run pytest tests/test_profiles.py -q`
Expected: PASS。
Run: `uv run resume-os --help`
Expected: 顯示 `profile` command。

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml uv.lock .gitignore src/resume_os tests/test_profiles.py
git commit -m "feat: add isolated resume profiles"
```

## Task 2：Canonical Store 與版本歷史

**Dependencies:** Task 1
**Acceptance:** 每個 profile 自己初始化 schema；entity、evidence、proposal、conflict、version 都在同一 transaction 邊界；不能跨 DB 查詢。
**Gate:** `schema_gate`。

**Files:**
- Create: `src/resume_os/models.py`
- Create: `src/resume_os/database.py`
- Test: `tests/test_database.py`

- [ ] **Step 1: 建立 canonical/version 失敗測試**

```python
# tests/test_database.py
from pathlib import Path

from resume_os.database import ResumeDatabase
from resume_os.models import EntityKind


def test_entity_update_preserves_version_history(tmp_path: Path) -> None:
    db = ResumeDatabase(tmp_path / "resume.sqlite")
    entity_id = db.create_entity(EntityKind.PROJECT, "project:mdreport2", {"name": "MDreport2"})
    db.replace_entity(entity_id, {"name": "MDreport2", "users": "5-10"}, reason="confirmed")

    assert db.get_entity(entity_id)["users"] == "5-10"
    versions = db.list_versions(entity_id)
    assert [item["snapshot"]["users"] for item in versions] == ["5-10"]
```

- [ ] **Step 2: 執行 RED**

Run: `uv run pytest tests/test_database.py -q`
Expected: FAIL，缺少 `ResumeDatabase`。

- [ ] **Step 3: 定義 schemas**

```python
# src/resume_os/models.py
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


class EntityKind(StrEnum):
    BASICS = "basics"
    EXPERIENCE = "experience"
    PROJECT = "project"
    EDUCATION = "education"
    SKILL = "skill"


class Evidence(BaseModel):
    entity_id: str | None = None
    field_path: str
    source_type: Literal["104", "interview", "github", "approved_version"]
    source_ref: str
    content: str
    contribution_type: Literal[
        "fact", "owner_decision", "business_rule", "validation", "ai_assisted_implementation"
    ] = "fact"


class ChangeProposal(BaseModel):
    entity_id: str
    field_path: str
    before: Any
    after: Any
    reason: str
    evidence_ids: list[str] = Field(min_length=1)
    risk_flags: list[str] = []
    status: Literal["pending", "accepted", "rejected", "edited", "blocked"] = "pending"
```

- [ ] **Step 4: 實作 SQLite schema 與 transaction API**

`ResumeDatabase` 必須建立 `entities`、`evidence`、`proposals`、`conflicts`、`versions`、`sources` 六張表；JSON 欄位以 `json.dumps(payload, ensure_ascii=False, sort_keys=True)` 寫入。`replace_entity()` 必須在單一 transaction 更新 entity 並新增 version，失敗時 rollback。

Public methods 固定為：

```python
# src/resume_os/database.py
import json
import sqlite3
from pathlib import Path
from uuid import uuid4

from resume_os.models import EntityKind

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS entities (
  id TEXT PRIMARY KEY, kind TEXT NOT NULL, stable_key TEXT NOT NULL UNIQUE,
  payload_json TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS evidence (
  id TEXT PRIMARY KEY, entity_id TEXT, field_path TEXT NOT NULL,
  source_type TEXT NOT NULL, source_ref TEXT NOT NULL, content TEXT NOT NULL,
  contribution_type TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(entity_id) REFERENCES entities(id)
);
CREATE TABLE IF NOT EXISTS proposals (
  id TEXT PRIMARY KEY, entity_id TEXT NOT NULL, field_path TEXT NOT NULL,
  before_json TEXT NOT NULL, after_json TEXT NOT NULL, reason TEXT NOT NULL,
  evidence_ids_json TEXT NOT NULL, risk_flags_json TEXT NOT NULL, status TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(entity_id) REFERENCES entities(id)
);
CREATE TABLE IF NOT EXISTS conflicts (
  id TEXT PRIMARY KEY, entity_id TEXT NOT NULL, field_path TEXT NOT NULL,
  current_json TEXT NOT NULL, candidate_json TEXT NOT NULL, question TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'open', answer_json TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(entity_id) REFERENCES entities(id)
);
CREATE TABLE IF NOT EXISTS versions (
  id TEXT PRIMARY KEY, entity_id TEXT NOT NULL, snapshot_json TEXT NOT NULL,
  reason TEXT NOT NULL, proposal_id TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(entity_id) REFERENCES entities(id)
);
CREATE TABLE IF NOT EXISTS sources (
  id TEXT PRIMARY KEY, source_type TEXT NOT NULL, source_ref TEXT NOT NULL,
  raw_path TEXT NOT NULL, sha256 TEXT NOT NULL, status TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


class ResumeDatabase:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript(SCHEMA)

    @staticmethod
    def _json(payload: object) -> str:
        return json.dumps(payload, ensure_ascii=False, sort_keys=True)

    def create_entity(self, kind: EntityKind, stable_key: str, payload: dict) -> str:
        entity_id = str(uuid4())
        with self.connection:
            self.connection.execute(
                "INSERT INTO entities(id,kind,stable_key,payload_json) VALUES(?,?,?,?)",
                (entity_id, kind.value, stable_key, self._json(payload)),
            )
        return entity_id

    def find_entity(self, kind: EntityKind, stable_key: str) -> tuple[str, dict] | None:
        row = self.connection.execute(
            "SELECT id,payload_json FROM entities WHERE kind=? AND stable_key=?",
            (kind.value, stable_key),
        ).fetchone()
        return None if row is None else (row["id"], json.loads(row["payload_json"]))

    def get_entity(self, entity_id: str) -> dict:
        row = self.connection.execute(
            "SELECT payload_json FROM entities WHERE id=?", (entity_id,)
        ).fetchone()
        if row is None:
            raise KeyError(entity_id)
        return json.loads(row["payload_json"])

    def replace_entity(
        self, entity_id: str, payload: dict, *, reason: str, proposal_id: str | None = None
    ) -> None:
        version_id = str(uuid4())
        encoded = self._json(payload)
        with self.connection:
            cursor = self.connection.execute(
                "UPDATE entities SET payload_json=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (encoded, entity_id),
            )
            if cursor.rowcount != 1:
                raise KeyError(entity_id)
            self.connection.execute(
                "INSERT INTO versions(id,entity_id,snapshot_json,reason,proposal_id) VALUES(?,?,?,?,?)",
                (version_id, entity_id, encoded, reason, proposal_id),
            )

    def list_versions(self, entity_id: str) -> list[dict]:
        rows = self.connection.execute(
            "SELECT snapshot_json,reason,proposal_id,created_at FROM versions WHERE entity_id=? ORDER BY created_at,id",
            (entity_id,),
        ).fetchall()
        return [
            {
                "snapshot": json.loads(row["snapshot_json"]),
                "reason": row["reason"],
                "proposal_id": row["proposal_id"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]
```

- [ ] **Step 5: 執行 GREEN**

Run: `uv run pytest tests/test_database.py -q`
Expected: PASS。

- [ ] **Step 6: Commit**

```bash
git add src/resume_os/models.py src/resume_os/database.py tests/test_database.py
git commit -m "feat: add canonical resume store"
```

## Task 3：來源匯入與 fallback

**Dependencies:** Task 2
**Acceptance:** 文字與公開 104 HTML 可建立 source artifact；URL 失敗回傳明確 fallback 選項；PDF 可抽文字；原始來源永遠保存。
**Gate:** `trace_gate`，每次匯入都有 source id、type、status、sha256。

**Files:**
- Create: `src/resume_os/sources.py`
- Create: `tests/fixtures/104_public_sample.html`
- Test: `tests/test_sources.py`

- [ ] **Step 1: 建立匯入失敗測試**

```python
# tests/test_sources.py
from pathlib import Path

import httpx

from resume_os.sources import ImportStatus, SourceImporter


def test_url_failure_returns_pdf_and_text_fallback(tmp_path: Path) -> None:
    def fail(_: str) -> httpx.Response:
        return httpx.Response(403, text="forbidden")

    result = SourceImporter(tmp_path, fetch=fail).from_url("https://example.invalid/resume")
    assert result.status == ImportStatus.NEEDS_FALLBACK
    assert result.fallbacks == ["pdf", "text"]


def test_html_import_keeps_original_and_extracts_visible_text(tmp_path: Path) -> None:
    html = "<html><body><main><h1>王小明</h1><p>專案經理</p></main></body></html>"
    result = SourceImporter(tmp_path).from_html(html, source_ref="fixture")
    assert "王小明" in result.text
    assert result.raw_path.read_text("utf-8") == html
```

- [ ] **Step 2: 執行 RED**

Run: `uv run pytest tests/test_sources.py -q`
Expected: FAIL，缺少 `SourceImporter`。

- [ ] **Step 3: 實作 source result 與 importer**

```python
# src/resume_os/sources.py
import hashlib
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Callable

import httpx
from bs4 import BeautifulSoup
from pypdf import PdfReader


class ImportStatus(StrEnum):
    READY = "ready"
    NEEDS_FALLBACK = "needs_fallback"


@dataclass(frozen=True)
class ImportResult:
    status: ImportStatus
    text: str = ""
    raw_path: Path | None = None
    sha256: str = ""
    fallbacks: list[str] | None = None


class SourceImporter:
    def __init__(self, source_dir: Path, fetch: Callable[[str], httpx.Response] | None = None) -> None:
        self.source_dir = source_dir
        self.source_dir.mkdir(parents=True, exist_ok=True)
        self.fetch = fetch or (lambda url: httpx.get(url, follow_redirects=True, timeout=15))

    def _save(self, content: bytes, suffix: str) -> tuple[Path, str]:
        digest = hashlib.sha256(content).hexdigest()
        path = self.source_dir / f"{digest}{suffix}"
        path.write_bytes(content)
        return path, digest

    def from_html(self, html: str, *, source_ref: str) -> ImportResult:
        path, digest = self._save(html.encode(), ".html")
        text = "\n".join(BeautifulSoup(html, "html.parser").stripped_strings)
        return ImportResult(ImportStatus.READY, text, path, digest, [])

    def from_url(self, url: str) -> ImportResult:
        response = self.fetch(url)
        if response.status_code != 200:
            return ImportResult(ImportStatus.NEEDS_FALLBACK, fallbacks=["pdf", "text"])
        return self.from_html(response.text, source_ref=url)

    def from_text(self, text: str) -> ImportResult:
        path, digest = self._save(text.encode(), ".txt")
        return ImportResult(ImportStatus.READY, text, path, digest, [])

    def from_pdf(self, path: Path) -> ImportResult:
        raw, digest = self._save(path.read_bytes(), ".pdf")
        text = "\n".join(page.extract_text() or "" for page in PdfReader(raw).pages)
        return ImportResult(ImportStatus.READY, text, raw, digest, [])
```

- [ ] **Step 4: 執行 GREEN**

Run: `uv run pytest tests/test_sources.py -q`
Expected: PASS。

- [ ] **Step 5: Checkpoint 1**

Run: `uv run pytest -q && git diff --check`
Expected: 全部 PASS；profile 與 source fixture 不互相讀取。

- [ ] **Step 6: Commit**

```bash
git add src/resume_os/sources.py tests/test_sources.py tests/fixtures/104_public_sample.html
git commit -m "feat: import local resume sources"
```

## Task 4：Canonical Merge 與衝突質問

**Dependencies:** Task 3
**Acceptance:** 同一事件更新原 entity；無衝突欄位可補充；日期、數字、角色與成果矛盾時建立 conflict 並保持原值。
**Gate:** `recompute_gate`。

**Files:**
- Create: `src/resume_os/merge.py`
- Test: `tests/test_merge.py`

- [ ] **Step 1: 建立去重與衝突失敗測試**

```python
# tests/test_merge.py
from resume_os.merge import merge_candidate


def test_same_project_is_enriched_not_duplicated() -> None:
    current = {"name": "MDreport2", "duration": "約兩個月"}
    candidate = {"name": "MDreport2", "users": "5-10 人"}
    result = merge_candidate(current, candidate)
    assert result.merged == {"name": "MDreport2", "duration": "約兩個月", "users": "5-10 人"}
    assert result.conflicts == []


def test_conflicting_metric_creates_question_and_preserves_current() -> None:
    current = {"monthly_hours_saved": "42-54"}
    candidate = {"monthly_hours_saved": "80"}
    result = merge_candidate(current, candidate)
    assert result.merged["monthly_hours_saved"] == "42-54"
    assert result.conflicts[0].question.startswith("目前記錄為 42-54")
```

- [ ] **Step 2: 執行 RED**

Run: `uv run pytest tests/test_merge.py -q`
Expected: FAIL。

- [ ] **Step 3: 實作 field-aware merge**

```python
# src/resume_os/merge.py
from dataclasses import dataclass

CONFLICT_FIELDS = {"date", "start_date", "end_date", "duration", "role", "result", "users", "monthly_hours_saved"}


@dataclass(frozen=True)
class ConflictCandidate:
    field: str
    current: object
    candidate: object
    question: str


@dataclass(frozen=True)
class MergeResult:
    merged: dict
    conflicts: list[ConflictCandidate]


def merge_candidate(current: dict, candidate: dict) -> MergeResult:
    merged = dict(current)
    conflicts = []
    for field, value in candidate.items():
        if field not in merged or merged[field] in (None, "", []):
            merged[field] = value
        elif merged[field] != value and field in CONFLICT_FIELDS:
            conflicts.append(ConflictCandidate(
                field, merged[field], value,
                f"目前記錄為 {merged[field]}，新資料是 {value}；哪一個才是最新版？",
            ))
        elif merged[field] == value:
            continue
    return MergeResult(merged, conflicts)
```

- [ ] **Step 4: 把 merge result 寫入 DB：無 conflict 才 replace；有 conflict 則建立 `conflicts` row，entity 不變**

- [ ] **Step 5: 執行 GREEN**

Run: `uv run pytest tests/test_merge.py tests/test_database.py -q`
Expected: PASS。

- [ ] **Step 6: Commit**

```bash
git add src/resume_os/merge.py src/resume_os/database.py tests/test_merge.py tests/test_database.py
git commit -m "feat: merge canonical facts with conflict questions"
```

## Task 5：Evidence Guard、修改提案與核准

**Dependencies:** Task 4
**Acceptance:** 無證據的新數字、技能、證照、職稱與工程 ownership 會 blocked；accepted 才更新 canonical；rejected 不更新；edited 必須重新過 guard。
**Gate:** `schema_gate` + `trace_gate`。

**Files:**
- Create: `src/resume_os/evidence.py`
- Create: `src/resume_os/proposals.py`
- Test: `tests/test_proposals.py`

- [ ] **Step 1: 建立 guard／approval 失敗測試**

```python
# tests/test_proposals.py
from resume_os.evidence import unsupported_claims


def test_ai_implementation_cannot_be_rewritten_as_personal_engineering() -> None:
    before = "以 PM 方式透過 AI 協作完成產品"
    after = "獨立設計並開發完整機器學習架構"
    evidence = ["contribution_type=owner_decision", "contribution_type=ai_assisted_implementation"]
    assert "engineering_ownership" in unsupported_claims(before, after, evidence)


def test_new_metric_without_evidence_is_blocked() -> None:
    assert "unsupported_number" in unsupported_claims("改善流程", "提升效率 80%", [])
```

- [ ] **Step 2: 執行 RED**

Run: `uv run pytest tests/test_proposals.py -q`
Expected: FAIL。

- [ ] **Step 3: 實作 deterministic claim extractor**

```python
# src/resume_os/evidence.py
import re

NUMBER = re.compile(r"(?<!\w)\d+(?:\.\d+)?(?:%|人|小時|天|個月|年|萬|億)?")
ENGINEERING_OWNERSHIP = ("獨立開發", "親自開發", "設計並開發", "架構並實作")


def unsupported_claims(before: str, after: str, evidence: list[str]) -> list[str]:
    risks = []
    new_numbers = set(NUMBER.findall(after)) - set(NUMBER.findall(before))
    if new_numbers and not any(number in item for number in new_numbers for item in evidence):
        risks.append("unsupported_number")
    if any(phrase in after for phrase in ENGINEERING_OWNERSHIP):
        has_ai_help = any("ai_assisted_implementation" in item for item in evidence)
        has_personal_code = any("personal_implementation" in item for item in evidence)
        if has_ai_help and not has_personal_code:
            risks.append("engineering_ownership")
    return risks
```

- [ ] **Step 4: 實作 proposal lifecycle**

`ProposalService.create()` 執行 guard；有 risks 時狀態為 `blocked`。`accept()` 只接受 `pending`，在 transaction 內更新 entity 與 version。`reject()` 只改 proposal 狀態。`edit()` 以使用者文字重跑 guard，通過後狀態為 `edited`，再要求一次 accept。

- [ ] **Step 5: 執行 GREEN**

Run: `uv run pytest tests/test_proposals.py -q`
Expected: PASS。

- [ ] **Step 6: Commit**

```bash
git add src/resume_os/evidence.py src/resume_os/proposals.py src/resume_os/database.py tests/test_proposals.py
git commit -m "feat: guard and approve resume changes"
```

## Task 6：104 輸出與五項評估

**Dependencies:** Task 5
**Acceptance:** 只輸出 accepted canonical data；五項評估都有 evidence-based reason，不產生總分。
**Gate:** `recompute_gate`。

**Files:**
- Create: `src/resume_os/evaluation.py`
- Create: `src/resume_os/export_104.py`
- Test: `tests/test_export_104.py`

- [ ] **Step 1: 建立輸出與評估失敗測試**

```python
# tests/test_export_104.py
from resume_os.evaluation import evaluate_resume
from resume_os.export_104 import render_104


def test_render_104_keeps_pm_and_ai_contribution_truthful() -> None:
    entities = [{
        "kind": "project",
        "name": "NEW-TOP10",
        "role": "以 PM 方式定義需求、規則與驗收，透過 AI 協作完成實作",
        "result": "每日選股、歷史回測與模擬追蹤",
    }]
    output = render_104(entities)
    assert "以 PM 方式" in output
    assert "獨立開發機器學習架構" not in output


def test_evaluation_has_five_dimensions_and_no_total_score() -> None:
    result = evaluate_resume([{"kind": "project", "name": "MDreport2", "evidence_count": 3}])
    assert set(result) == {"parseability", "role_clarity", "outcome_evidence", "skills", "credibility"}
    assert "total" not in result
```

- [ ] **Step 2: 執行 RED**

Run: `uv run pytest tests/test_export_104.py -q`
Expected: FAIL。

- [ ] **Step 3: 實作 exporter 與 rubric**

`render_104()` 固定輸出「求職方向、工作經歷、專案成果、技能、學歷」區段；缺區段則省略，不生成空話。`evaluate_resume()` 每個維度回傳 `{status: strong|needs_review|missing, reasons: list[str], entity_ids: list[str]}`，不得回傳數字總分。

- [ ] **Step 4: 執行 GREEN**

Run: `uv run pytest tests/test_export_104.py -q`
Expected: PASS。

- [ ] **Step 5: Checkpoint 2**

Run: `uv run pytest -q && uv run resume-os --help && git diff --check`
Expected: 全部 PASS；資料層已能從 source 走到 approved export。

- [ ] **Step 6: Commit**

```bash
git add src/resume_os/evaluation.py src/resume_os/export_104.py tests/test_export_104.py
git commit -m "feat: export verified 104 resume content"
```

## Task 7：CLI 完整工作流與 Codex Skill

**Dependencies:** Task 6
**Acceptance:** CLI 可完成 status、source import、entity list、conflict answer、proposal create/list/accept/reject/edit、export；Skill 強制選 profile、逐題問、只呼叫 deterministic mutation。
**Gate:** `cmd_gate`。

**Files:**
- Modify: `src/resume_os/cli.py`
- Create: `.codex/skills/resume-os/SKILL.md`
- Create: `.codex/skills/resume-os/agents/openai.yaml`
- Create: `.codex/skills/resume-os/references/workflow.md`
- Test: `tests/test_cli_flow.py`
- Test: `tests/test_skill_contract.py`

- [ ] **Step 1: 建立 CLI E2E 失敗測試**

```python
# tests/test_cli_flow.py
from pathlib import Path

from resume_os.cli import run


def test_cli_blocks_write_without_active_profile(tmp_path: Path) -> None:
    result = run(["proposal", "list"], workspace=tmp_path)
    assert result.exit_code == 2
    assert "select a profile" in result.stderr


def test_cli_profile_source_to_export_flow(tmp_path: Path) -> None:
    assert run(["profile", "create", "matt", "--display-name", "Matt"], workspace=tmp_path).exit_code == 0
    assert run(["profile", "select", "matt"], workspace=tmp_path).exit_code == 0
    source = tmp_path / "resume.txt"
    source.write_text("專案經理｜負責 DSP 與 SSP 報表", encoding="utf-8")
    assert run(["source", "import-text", str(source)], workspace=tmp_path).exit_code == 0
    assert run(["status"], workspace=tmp_path).stdout_json["active_profile"] == "matt"
```

- [ ] **Step 2: 執行 RED**

Run: `uv run pytest tests/test_cli_flow.py -q`
Expected: FAIL，現有 CLI 無 `run()` 與 commands。

- [ ] **Step 3: 把 CLI 改為可測試的 `run(argv, workspace) -> CommandResult`，`main()` 只負責輸出與 exit**

所有 machine-readable commands 支援 `--json`，錯誤格式固定為：

```json
{"status":"error","error_code":"NO_ACTIVE_PROFILE","message":"select a profile before reading or writing resume data","details":{}}
```

- [ ] **Step 4: RED：建立 Skill contract tests，尚未建立 SKILL.md 時必須失敗**

```python
# tests/test_skill_contract.py
from pathlib import Path


def test_skill_requires_profile_evidence_and_human_approval() -> None:
    text = Path(".codex/skills/resume-os/SKILL.md").read_text("utf-8")
    assert "profile" in text
    assert "Evidence Guard" in text
    assert "一次只問一個關鍵問題" in text
    assert "不得直接寫入 Master Resume" in text
    assert "修改前" in text and "修改後" in text and "修改理由" in text
```

Run: `uv run pytest tests/test_skill_contract.py -q`
Expected: FAIL，SKILL.md 不存在。

- [ ] **Step 5: 使用 skill-creator 初始化 repo-local Skill**

Run:

```bash
python3 "$HOME/.codex/skills/.system/skill-creator/scripts/init_skill.py" resume-os \
  --path .codex/skills \
  --resources references \
  --interface display_name="Resume OS" \
  --interface short_description="以證據約束方式修改繁中 104 履歷" \
  --interface default_prompt="使用 Resume OS 選擇人物並開始履歷訪談。"
```

Expected: 建立 `SKILL.md`、`agents/openai.yaml`、`references/`。

- [ ] **Step 6: 寫入最小 Skill workflow**

SKILL.md 必須保持小於 500 行，frontmatter description 只寫觸發條件：

```markdown
---
name: resume-os
description: Use when importing, reviewing, interviewing for, revising, comparing, or exporting a Traditional Chinese 104 resume or a local Master Resume.
---

# Resume OS

先執行 `uv run resume-os status --json`。沒有 active profile 時，只能建立或選擇人物，不得讀寫履歷。

1. 匯入 104 URL；失敗時提供 PDF 與文字 fallback。
2. 只載入 active profile。人物資料不得交叉引用。
3. 解析結果先作候選；不確定欄位要顯示原文並詢問。
4. 關鍵缺口一次只問一個問題；簡單欄位可集中詢問。
5. 新舊資料衝突時先質問，不覆蓋 canonical 值。
6. 每個修改提案必須顯示修改前、修改後、修改理由與 evidence。
7. 先跑 Evidence Guard。Blocked proposal 不得要求使用者接受。
8. 只有使用者明確接受的 proposal 才能寫入 Master Resume。

程式由 AI 協助時，只能描述使用者的問題定義、規則、決策與驗收；不得改寫為本人手寫工程架構。

CLI artifact 與錯誤格式請讀 `references/workflow.md`。
```

- [ ] **Step 7: Skill RED/GREEN 壓力測試**

依 `writing-skills` 執行三個隔離情境：

1. 未選 profile，使用者要求「先幫我快速改」；預期拒絕寫入並要求選 profile。
2. GitHub 顯示大量 ML code，但 evidence 是 AI-assisted implementation；預期不得寫成 ML engineer。
3. 新答案的數字與舊值矛盾且使用者催促直接採用；預期先提出 conflict question。

若要使用 subagent forward-test，執行前需取得使用者對該測試的明確同意；未取得同意時，不得宣稱完成 Skill forward-test。

- [ ] **Step 8: 驗證 Skill 與 CLI**

Run:

```bash
python3 "$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py" .codex/skills/resume-os
uv run pytest tests/test_cli_flow.py tests/test_skill_contract.py -q
```

Expected: `Skill is valid!` 且 tests PASS。

- [ ] **Step 9: Commit**

```bash
git add src/resume_os/cli.py .codex/skills/resume-os tests/test_cli_flow.py tests/test_skill_contract.py
git commit -m "feat: add Resume OS Codex workflow"
```

## Task 8：雙人物端到端驗收

**Dependencies:** Task 7
**Acceptance:** synthetic 自動驗收通過；接著依序用產品本人與一位朋友的真實 104 履歷驗證。未取得朋友履歷前，只能標示 `waiting_for_fixture`，不能宣稱 MVP 全部完成。
**Gate:** `trace_gate` + human approval。

**Files:**
- Create: `tests/fixtures/matt_candidate.json`
- Create: `tests/fixtures/friend_candidate.json`
- Create: `tests/test_acceptance.py`
- Create: `docs/acceptance/resume-os-mvp-checklist.md`

- [ ] **Step 1: 建立兩人物隔離 acceptance test**

```python
# tests/test_acceptance.py
def test_two_profiles_never_share_entities(acceptance_workspace) -> None:
    matt = acceptance_workspace.profile("matt")
    friend = acceptance_workspace.profile("friend-a")
    matt.add_project("MDreport2")
    friend.add_experience("Friend Company")

    assert "Friend Company" not in matt.export_104()
    assert "MDreport2" not in friend.export_104()


def test_rejected_and_blocked_proposals_never_reach_export(acceptance_workspace) -> None:
    matt = acceptance_workspace.profile("matt")
    blocked = matt.propose("project.role", "獨立開發完整機器學習架構", evidence=[])
    rejected = matt.propose("project.result", "提升 80%", evidence=["unrelated"])
    matt.reject(rejected.id)

    output = matt.export_104()
    assert blocked.status == "blocked"
    assert "機器學習架構" not in output
    assert "80%" not in output
```

- [ ] **Step 2: 執行自動 acceptance**

Run: `uv run pytest tests/test_acceptance.py -q`
Expected: PASS。

- [ ] **Step 3: 產品本人真實履歷驗收**

使用真實 104 URL；若 URL 不可讀，記錄 fallback 證據並改用 PDF／文字。至少驗證 `MDreport2`、`IAS-Dashboard`、`NEW-TOP10` 三個案例，且輸出不得把 AI-assisted implementation 寫成本人工程實作。

- [ ] **Step 4: 朋友真實履歷驗收**

建立新的 profile，不複製產品本人資料。完成一次來源匯入、至少一個 conflict 或缺口問題、至少一項 accepted proposal、一項 rejected proposal，以及 104 export。

- [ ] **Step 5: Checkpoint 3／完成閘門**

Run:

```bash
uv run pytest -q
python3 "$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py" .codex/skills/resume-os
git diff --check
git status --short
```

Expected: tests PASS、Skill valid、diff check 無輸出；真實 acceptance checklist 由使用者確認。未提供朋友履歷時，狀態必須保持 `waiting_for_fixture`。

- [ ] **Step 6: Commit**

```bash
git add tests/fixtures tests/test_acceptance.py docs/acceptance/resume-os-mvp-checklist.md
git commit -m "test: verify Resume OS profile isolation"
```

## 計畫自審

- Spec coverage：人物隔離、來源 fallback、canonical merge、衝突質問、Evidence Guard、逐項核准、版本、104 輸出、五項評估、兩位真實使用者皆有對應 Task。
- Deterministic／LLM boundary：LLM 只提出問題與文字候選；profile selection、merge、conflict、guard、approval、version、export 都由 Python deterministic core 執行。
- Mutation boundary：所有寫入都要求 active profile；proposal accept 是唯一 canonical mutation 入口。
- Remaining external dependency：真實 104 頁面可讀性及朋友履歷要在 Task 8 提供，否則只能完成自動測試，不能宣稱真實驗收完成。
