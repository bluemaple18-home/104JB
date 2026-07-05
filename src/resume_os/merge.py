from dataclasses import dataclass

CONFLICT_FIELDS = {
    "date",
    "start_date",
    "end_date",
    "duration",
    "role",
    "result",
    "users",
    "monthly_hours_saved",
}


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
            conflicts.append(
                ConflictCandidate(
                    field,
                    merged[field],
                    value,
                    f"目前記錄為 {merged[field]}，新資料是 {value}；哪一個才是最新版？",
                )
            )
        elif merged[field] == value:
            continue
    return MergeResult(merged, conflicts)
