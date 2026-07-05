import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

from resume_os.database import ResumeDatabase
from resume_os.evaluation import evaluate_resume
from resume_os.export_104 import render_104
from resume_os.models import EntityKind, Evidence
from resume_os.profiles import NoActiveProfile, ProfileManager
from resume_os.proposals import ProposalService
from resume_os.sources import ImportResult, SourceImporter


@dataclass(frozen=True)
class CommandResult:
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    stdout_json: dict = field(default_factory=dict)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="resume-os")
    sub = parser.add_subparsers(dest="command", required=True)

    profile = sub.add_parser("profile")
    profile_actions = profile.add_subparsers(dest="action", required=True)
    create_profile = profile_actions.add_parser("create")
    create_profile.add_argument("slug")
    create_profile.add_argument("--display-name", required=True)
    profile_actions.add_parser("list")
    select_profile = profile_actions.add_parser("select")
    select_profile.add_argument("slug")

    sub.add_parser("status")

    source = sub.add_parser("source")
    source_actions = source.add_subparsers(dest="action", required=True)
    for action in ("import-text", "import-pdf"):
        command = source_actions.add_parser(action)
        command.add_argument("path")
    import_url = source_actions.add_parser("import-url")
    import_url.add_argument("url")

    entity = sub.add_parser("entity")
    entity_actions = entity.add_subparsers(dest="action", required=True)
    entity_actions.add_parser("list")
    add_entity = entity_actions.add_parser("add")
    add_entity.add_argument("kind", choices=[kind.value for kind in EntityKind])
    add_entity.add_argument("stable_key")
    add_entity.add_argument("--payload-json", required=True)

    conflict = sub.add_parser("conflict")
    conflict_actions = conflict.add_subparsers(dest="action", required=True)
    list_conflicts = conflict_actions.add_parser("list")
    list_conflicts.add_argument("--entity-id", required=True)
    answer_conflict = conflict_actions.add_parser("answer")
    answer_conflict.add_argument("conflict_id")
    answer_conflict.add_argument("--value-json", required=True)

    evidence = sub.add_parser("evidence")
    evidence_actions = evidence.add_subparsers(dest="action", required=True)
    add_evidence = evidence_actions.add_parser("add")
    add_evidence.add_argument("entity_id")
    add_evidence.add_argument("field_path")
    add_evidence.add_argument("--source-type", required=True, choices=["104", "interview", "github", "approved_version"])
    add_evidence.add_argument("--source-ref", required=True)
    add_evidence.add_argument("--content", required=True)
    add_evidence.add_argument(
        "--contribution-type",
        default="fact",
        choices=["fact", "owner_decision", "business_rule", "validation", "ai_assisted_implementation"],
    )

    proposal = sub.add_parser("proposal")
    proposal_actions = proposal.add_subparsers(dest="action", required=True)
    proposal_actions.add_parser("list")
    create_proposal = proposal_actions.add_parser("create")
    create_proposal.add_argument("entity_id")
    create_proposal.add_argument("field_path")
    create_proposal.add_argument("--after-json", required=True)
    create_proposal.add_argument("--reason", required=True)
    create_proposal.add_argument("--evidence-id", action="append", default=[])
    for action in ("accept", "reject"):
        command = proposal_actions.add_parser(action)
        command.add_argument("proposal_id")
    edit_proposal = proposal_actions.add_parser("edit")
    edit_proposal.add_argument("proposal_id")
    edit_proposal.add_argument("--after-json", required=True)

    export = sub.add_parser("export")
    export.add_argument("format", choices=["104"])
    sub.add_parser("evaluate")
    return parser


def _success(payload: dict, *, stdout: str | None = None) -> CommandResult:
    rendered = json.dumps(payload, ensure_ascii=False) if stdout is None else stdout
    return CommandResult(0, stdout=rendered, stdout_json=payload)


def _record_import(
    db: ResumeDatabase, profile_root: Path, result: ImportResult, source_type: str, source_ref: str
) -> dict:
    raw_path = ""
    if result.raw_path is not None:
        raw_path = str(result.raw_path.relative_to(profile_root))
    source_id = db.add_source(
        source_type=source_type,
        source_ref=source_ref,
        raw_path=raw_path,
        sha256=result.sha256,
        status=result.status.value,
    )
    return {
        "source_id": source_id,
        "status": result.status.value,
        "sha256": result.sha256,
        "raw_path": raw_path,
        "fallbacks": result.fallbacks or [],
        "text": result.text,
    }


def run(argv: list[str], *, workspace: Path) -> CommandResult:
    args = _parser().parse_args([item for item in argv if item != "--json"])
    manager = ProfileManager(workspace)
    try:
        if args.command == "profile":
            if args.action == "create":
                profile = manager.create(args.slug, args.display_name)
                return _success({"slug": profile.slug, "display_name": profile.display_name})
            if args.action == "select":
                profile = manager.select(args.slug)
                return _success({"active_profile": profile.slug})
            return _success(
                {"profiles": [{"slug": item.slug, "display_name": item.display_name} for item in manager.list()]}
            )

        profile = manager.active()
        db = ResumeDatabase(profile.database_path)
        if args.command == "status":
            return _success(
                {
                    "active_profile": profile.slug,
                    "entity_count": len(db.list_entities()),
                    "source_count": len(db.list_sources()),
                    "proposal_count": len(ProposalService(db).list()),
                }
            )
        if args.command == "source":
            importer = SourceImporter(profile.root / "sources")
            if args.action == "import-text":
                path = Path(args.path)
                result = importer.from_text(path.read_text("utf-8"))
                return _success(_record_import(db, profile.root, result, "text", str(path)))
            if args.action == "import-pdf":
                path = Path(args.path)
                result = importer.from_pdf(path)
                return _success(_record_import(db, profile.root, result, "pdf", str(path)))
            result = importer.from_url(args.url)
            return _success(_record_import(db, profile.root, result, "104", args.url))
        if args.command == "entity":
            if args.action == "add":
                entity_id = db.create_entity(
                    EntityKind(args.kind), args.stable_key, json.loads(args.payload_json)
                )
                return _success({"entity_id": entity_id})
            return _success({"entities": db.list_entities()})
        if args.command == "conflict":
            if args.action == "answer":
                return _success(db.answer_conflict(args.conflict_id, json.loads(args.value_json)))
            return _success({"conflicts": db.list_conflicts(args.entity_id)})
        if args.command == "evidence":
            evidence_id = db.add_evidence(
                Evidence(
                    entity_id=args.entity_id,
                    field_path=args.field_path,
                    source_type=args.source_type,
                    source_ref=args.source_ref,
                    content=args.content,
                    contribution_type=args.contribution_type,
                )
            )
            return _success({"evidence_id": evidence_id})
        if args.command == "proposal":
            service = ProposalService(db)
            if args.action == "list":
                return _success({"proposals": service.list()})
            if args.action == "create":
                return _success(
                    service.create(
                        args.entity_id,
                        args.field_path,
                        json.loads(args.after_json),
                        reason=args.reason,
                        evidence_ids=args.evidence_id,
                    )
                )
            if args.action == "accept":
                return _success(service.accept(args.proposal_id))
            if args.action == "reject":
                return _success(service.reject(args.proposal_id))
            return _success(service.edit(args.proposal_id, json.loads(args.after_json)))
        if args.command == "export":
            output = render_104(db.list_entities())
            return _success({"format": "104", "output": output}, stdout=output)
        return _success({"evaluation": evaluate_resume(db.list_entities())})
    except NoActiveProfile as error:
        payload = {
            "status": "error",
            "error_code": "NO_ACTIVE_PROFILE",
            "message": str(error),
            "details": {},
        }
        return CommandResult(2, stderr=str(error), stdout_json=payload)
    except (FileNotFoundError, KeyError, ValueError, json.JSONDecodeError) as error:
        payload = {
            "status": "error",
            "error_code": "COMMAND_ERROR",
            "message": str(error),
            "details": {},
        }
        return CommandResult(1, stderr=str(error), stdout_json=payload)


def main() -> None:
    argv = sys.argv[1:]
    result = run(argv, workspace=Path.cwd())
    if "--json" in argv:
        print(json.dumps(result.stdout_json, ensure_ascii=False))
    elif result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    if result.exit_code:
        raise SystemExit(result.exit_code)
