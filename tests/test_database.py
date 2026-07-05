from pathlib import Path

import pytest

from resume_os.database import ResumeDatabase
from resume_os.models import EntityKind


def test_entity_update_preserves_version_history(tmp_path: Path) -> None:
    db = ResumeDatabase(tmp_path / "resume.sqlite")
    entity_id = db.create_entity(EntityKind.PROJECT, "project:mdreport2", {"name": "MDreport2"})
    db.replace_entity(entity_id, {"name": "MDreport2", "users": "5-10"}, reason="confirmed")

    assert db.get_entity(entity_id)["users"] == "5-10"
    versions = db.list_versions(entity_id)
    assert [item["snapshot"]["users"] for item in versions] == ["5-10"]


def test_profile_databases_do_not_share_entities(tmp_path: Path) -> None:
    matt = ResumeDatabase(tmp_path / "matt" / "resume.sqlite")
    friend = ResumeDatabase(tmp_path / "friend-a" / "resume.sqlite")
    entity_id = matt.create_entity(EntityKind.PROJECT, "project:private", {"name": "Private"})

    assert matt.get_entity(entity_id)["name"] == "Private"
    with pytest.raises(KeyError):
        friend.get_entity(entity_id)


def test_missing_entity_update_does_not_create_version(tmp_path: Path) -> None:
    db = ResumeDatabase(tmp_path / "resume.sqlite")

    with pytest.raises(KeyError):
        db.replace_entity("missing", {"name": "Missing"}, reason="invalid")

    assert db.list_versions("missing") == []


def test_capability_profile_is_a_profile_scoped_canonical_entity(tmp_path: Path) -> None:
    matt = ResumeDatabase(tmp_path / "matt" / "resume.sqlite")
    friend = ResumeDatabase(tmp_path / "friend" / "resume.sqlite")
    entity_id = matt.create_entity(
        EntityKind.CAPABILITY,
        "capability:core",
        {"name": "Synthetic Capability Profile", "summary": "Cross-domain integration"},
    )

    assert matt.get_entity(entity_id)["summary"] == "Cross-domain integration"
    with pytest.raises(KeyError):
        friend.get_entity(entity_id)
