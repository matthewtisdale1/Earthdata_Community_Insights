import re
from typing import Optional

from fastapi import Query
from sqlalchemy import text

from app.main_similarity import app, engine


IMPLEMENTATION_PATTERNS = (
    r"\b(?:ESDIS|NASA|DAAC|ASDC|GES DISC|LP DAAC)\s+(?:should|must|needs? to)\b",
    r"\b(?:develop|create|build|implement|add|provide)\b",
    r"\brecommend(?:s|ed)? that\b",
)


def _recommend(statement: str) -> tuple[str, list[str]]:
    current = " ".join((statement or "").split())
    suggestion = current
    reasons: list[str] = []

    repairs = (
        (r"^Earthdata users need recommend that\s+", "Earthdata users need "),
        (r"^Earthdata users need recommendations? that\s+", "Earthdata users need "),
        (r"^Earthdata users need that\s+", "Earthdata users need "),
        (r"^Earthdata users needs? to\s+", "Earthdata users need to "),
        (r"^Users need\s+", "Earthdata users need "),
        (r"^The community needs\s+", "Earthdata users need "),
    )
    for pattern, replacement in repairs:
        updated = re.sub(pattern, replacement, suggestion, flags=re.IGNORECASE)
        if updated != suggestion:
            suggestion = updated
            reasons.append("Grammar or canonical-prefix correction")

    if not re.match(r"^Earthdata users need\b", suggestion, flags=re.IGNORECASE):
        suggestion = f"Earthdata users need {suggestion[0].lower() + suggestion[1:] if suggestion else ''}".strip()
        reasons.append("Does not use the canonical Earthdata-wide need format")

    for pattern in IMPLEMENTATION_PATTERNS:
        if re.search(pattern, current, flags=re.IGNORECASE):
            reasons.append("Contains implementation- or organization-specific language")
            break

    if len(current) > 280:
        reasons.append("Canonical statement is unusually long")
    if current.count(".") > 1 or ";" in current:
        reasons.append("May contain multiple outcomes")
    if not current.endswith((".", "?", "!")) and current:
        suggestion += "."
        reasons.append("Missing terminal punctuation")

    # Conservative wording repair for common malformed recommendation phrasing.
    suggestion = re.sub(
        r"^Earthdata users need (?:ESDIS|NASA|the DAAC) to develop\s+",
        "Earthdata users need ",
        suggestion,
        flags=re.IGNORECASE,
    )
    suggestion = re.sub(r"\s+", " ", suggestion).strip()
    return suggestion, list(dict.fromkeys(reasons))


@app.get('/curation/needs/recommendations')
def need_recommendations(
    q: str = '',
    issue: str = '',
    limit: int = Query(500, ge=1, le=500),
):
    conditions = ['1=1']
    parameters = {'limit': limit}
    if q:
        conditions.append('(n.need_code LIKE :search OR n.canonical_need LIKE :search)')
        parameters['search'] = f'%{q}%'

    with engine.connect() as connection:
        rows = connection.execute(text(f'''
            SELECT n.need_code, n.canonical_need, n.need_category,
                   n.lifecycle_status, n.human_reviewed, n.reviewer,
                   n.desired_outcome, n.notes,
                   COALESCE(v.evidence_count, 0) AS evidence_count,
                   COALESCE(v.organization_count, 0) AS organization_count,
                   COALESCE(v.year_count, 0) AS year_count
            FROM needs n
            LEFT JOIN v_need_summary v ON v.need_id = n.need_id
            WHERE {' AND '.join(conditions)}
            ORDER BY n.human_reviewed, n.need_code
            LIMIT :limit
        '''), parameters).mappings().all()

    recommendations = []
    for row in rows:
        recommendation, reasons = _recommend(row['canonical_need'])
        if not reasons:
            continue
        if issue and not any(issue.lower() in reason.lower() for reason in reasons):
            continue
        item = dict(row)
        item['recommended_canonical_need'] = recommendation
        item['recommendation_reasons'] = reasons
        item['recommendation_count'] = len(reasons)
        item['changed'] = recommendation != row['canonical_need']
        recommendations.append(item)
    return recommendations


@app.get('/curation/needs/recommendations/summary')
def need_recommendation_summary():
    with engine.connect() as connection:
        rows = connection.execute(text('''
            SELECT need_code, canonical_need FROM needs
        ''')).mappings().all()

    flagged = 0
    grammar = 0
    implementation = 0
    multi_outcome = 0
    for row in rows:
        _, reasons = _recommend(row['canonical_need'])
        if reasons:
            flagged += 1
        grammar += int(any('Grammar' in reason or 'format' in reason or 'punctuation' in reason for reason in reasons))
        implementation += int(any('implementation' in reason for reason in reasons))
        multi_outcome += int(any('multiple outcomes' in reason for reason in reasons))
    return {
        'total_needs': len(rows),
        'flagged_needs': flagged,
        'grammar_or_format': grammar,
        'implementation_language': implementation,
        'possible_multiple_outcomes': multi_outcome,
    }
