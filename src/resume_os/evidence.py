import re

NUMBER = re.compile(r"(?<!\w)\d+(?:\.\d+)?(?:%|人|小時|天|個月|年|萬|億)?")
ENGINEERING_OWNERSHIP = ("獨立開發", "親自開發", "設計並開發", "架構並實作")
HIGH_RISK_FIELDS = {
    "skill": "unsupported_skill",
    "skills": "unsupported_skill",
    "certification": "unsupported_certification",
    "certifications": "unsupported_certification",
    "certificate": "unsupported_certification",
    "job_title": "unsupported_title",
    "title": "unsupported_title",
    "company": "unsupported_company",
    "company_name": "unsupported_company",
    "date": "unsupported_date",
    "start_date": "unsupported_date",
    "end_date": "unsupported_date",
}


def unsupported_claims(
    before: str, after: str, evidence: list[str], *, field_path: str | None = None
) -> list[str]:
    risks = []
    new_numbers = set(NUMBER.findall(after)) - set(NUMBER.findall(before))
    if new_numbers and not all(any(number in item for item in evidence) for number in new_numbers):
        risks.append("unsupported_number")
    if any(phrase in after for phrase in ENGINEERING_OWNERSHIP):
        has_personal_code = any("personal_implementation" in item for item in evidence)
        if not has_personal_code:
            risks.append("engineering_ownership")
    field = "" if field_path is None else field_path.rsplit(".", 1)[-1]
    high_risk = HIGH_RISK_FIELDS.get(field)
    has_matching_evidence = any(after.casefold() in item.casefold() for item in evidence)
    if high_risk and before != after and not has_matching_evidence:
        risks.append(high_risk)
    return risks
