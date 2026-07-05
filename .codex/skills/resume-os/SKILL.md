---
name: resume-os
description: Use when importing, reviewing, interviewing for, revising, comparing, or exporting a Traditional Chinese 104 resume or a local Master Resume.
---

# Resume OS

## Core boundary

Use the LLM only to ask interview questions and draft candidate wording. Use `resume-os` deterministic CLI commands for profile selection, source trace, canonical merge, conflict resolution, Evidence Guard, approval, versioning, evaluation, and export.

Never treat model output as a verified fact. Never directly edit SQLite, profile files, or Master Resume content.

## Workflow

1. Run `uv run resume-os status --json`.
2. If no active profile exists, create or select one. Do not read or write resume data before explicit profile selection.
3. Import the 104 URL. If it returns `needs_fallback`, request a PDF or pasted text.
4. Treat parsed fields as candidates. Preserve uncertain source text and ask the user to confirm it.
5. Ask one critical question at a time（一次只問一個關鍵問題）. Simple factual fields may be grouped.
6. If old and new facts conflict, display the conflict question. Do not overwrite the canonical value before an answer.
7. Create proposals that show 修改前、修改後、修改理由 and evidence references.
8. Run Evidence Guard before asking for approval. A blocked proposal cannot be accepted.
9. Let the user accept, reject, or edit each proposal. Edited text must pass Evidence Guard again.
10. Only an explicit accepted proposal may update the Master Resume. 不得直接寫入 Master Resume.
11. Export only the active profile's approved canonical entities and present the five-part evaluation without a total score.

## Contribution truthfulness

When implementation was AI-assisted, preserve `ai_assisted_implementation`. Describe the user's problem definition, business rules, decisions, and validation; do not rewrite these as personal engineering architecture or coding ownership.

## Safety

- Never copy resume content, answers, evidence, versions, or assumptions across profiles.
- Never add unsupported companies, titles, dates, metrics, skills, certifications, outcomes, or ownership claims.
- Never log, commit, or export API keys or real profile databases into Git.
- Never automate login to or modification of 104.

Read [references/workflow.md](references/workflow.md) for CLI commands and JSON artifact contracts.
