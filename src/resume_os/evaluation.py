from typing import Literal

EvaluationStatus = Literal["strong", "needs_review", "missing"]


def _item(status: EvaluationStatus, reason: str, entity_ids: list[str]) -> dict:
    return {"status": status, "reasons": [reason], "entity_ids": entity_ids}


def evaluate_resume(entities: list[dict]) -> dict[str, dict]:
    entity_ids = [str(entity["id"]) for entity in entities if entity.get("id")]
    named = [entity for entity in entities if entity.get("kind") and entity.get("name")]
    roles = [entity for entity in entities if entity.get("role") or entity.get("title")]
    outcomes = [entity for entity in entities if entity.get("result")]
    skills = [entity for entity in entities if entity.get("kind") == "skill" or entity.get("skills")]
    evidenced = [entity for entity in entities if entity.get("evidence_count", 0) > 0]

    parseability = (
        _item("strong", "主要實體皆有可辨識的類型與名稱。", entity_ids)
        if entities and len(named) == len(entities)
        else _item("needs_review" if entities else "missing", "仍有實體缺少類型或可辨識名稱。", entity_ids)
    )
    role_clarity = (
        _item("strong", "工作或專案已記錄本人角色。", [str(e.get("id")) for e in roles if e.get("id")])
        if roles
        else _item("missing", "尚無足夠角色資料可供判定。", [])
    )
    outcome_evidence = (
        _item("strong", "已記錄專案或工作成果。", [str(e.get("id")) for e in outcomes if e.get("id")])
        if outcomes
        else _item("missing", "尚無可驗證的成果敘述。", [])
    )
    skill_status = (
        _item("strong", "技能已連結到 canonical 實體。", [str(e.get("id")) for e in skills if e.get("id")])
        if skills
        else _item("missing", "尚無有經歷支持的技能資料。", [])
    )
    credibility = (
        _item("strong", "至少一個實體有可追溯 evidence。", [str(e.get("id")) for e in evidenced if e.get("id")])
        if evidenced
        else _item("missing", "尚無足夠 evidence 可供追溯。", [])
    )
    return {
        "parseability": parseability,
        "role_clarity": role_clarity,
        "outcome_evidence": outcome_evidence,
        "skills": skill_status,
        "credibility": credibility,
    }
