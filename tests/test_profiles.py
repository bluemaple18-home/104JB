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
