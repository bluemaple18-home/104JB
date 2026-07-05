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
