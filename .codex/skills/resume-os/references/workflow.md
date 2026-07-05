# Resume OS CLI Workflow

Run commands from the repository root. Add `--json` anywhere in a command for machine-readable output.

## Profile and status

```bash
uv run resume-os profile create <slug> --display-name "<name>"
uv run resume-os profile list --json
uv run resume-os profile select <slug>
uv run resume-os status --json
```

All non-profile commands fail with `NO_ACTIVE_PROFILE` until selection is explicit.

## Source trace

```bash
uv run resume-os source import-url <104-url> --json
uv run resume-os source import-pdf <path> --json
uv run resume-os source import-text <path> --json
```

Each result includes `source_id`, `status`, `sha256`, and a profile-relative `raw_path`. URL failure returns `fallbacks: ["pdf", "text"]`.

## Canonical entities and evidence

```bash
uv run resume-os entity list --json
uv run resume-os entity add project project:<stable-key> --payload-json '<json>' --json
uv run resume-os evidence add <entity-id> <field-path> \
  --source-type interview --source-ref <ref> --content '<source text>' --json
```

Only use `entity add` for an initial canonical entity derived from preserved source material. Later changes must use proposals.

## Conflict and proposal lifecycle

```bash
uv run resume-os conflict list --entity-id <entity-id> --json
uv run resume-os conflict answer <conflict-id> --value-json '<json>' --json
uv run resume-os proposal create <entity-id> <field-path> \
  --after-json '<json>' --reason '<reason>' --evidence-id <evidence-id> --json
uv run resume-os proposal list --json
uv run resume-os proposal accept <proposal-id> --json
uv run resume-os proposal reject <proposal-id> --json
uv run resume-os proposal edit <proposal-id> --after-json '<json>' --json
```

`blocked` cannot be accepted. `edited` must be explicitly accepted after Evidence Guard reruns.

## Export and evaluation

```bash
uv run resume-os export 104
uv run resume-os evaluate --json
```

Export reads only canonical entities in the active profile. Evaluation returns `parseability`, `role_clarity`, `outcome_evidence`, `skills`, and `credibility`; it never returns a total score.

## Error contract

```json
{"status":"error","error_code":"NO_ACTIVE_PROFILE","message":"select a profile before reading or writing resume data","details":{}}
```
