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
