SECTION_TITLES = {
    "basics": "求職方向",
    "experience": "工作經歷",
    "project": "專案成果",
    "skill": "技能",
    "education": "學歷",
}

FIELD_ORDER = (
    "name",
    "target_role",
    "company",
    "title",
    "start_date",
    "end_date",
    "role",
    "result",
    "skills",
    "school",
    "degree",
)


def render_104(entities: list[dict]) -> str:
    sections = []
    for kind, title in SECTION_TITLES.items():
        lines = []
        for entity in entities:
            if entity.get("kind") != kind:
                continue
            values = [str(entity[field]) for field in FIELD_ORDER if entity.get(field)]
            if values:
                lines.append(f"- {'｜'.join(values)}")
        if lines:
            sections.append(f"## {title}\n" + "\n".join(lines))
    return "\n\n".join(sections)
