import re
from typing import Optional

from fastapi import Query
from sqlalchemy import text

from app.main_similarity import app, engine


IMPLEMENTATION_PATTERNS = (
    r"\b(?:ESDIS|NASA|DAAC|ASDC|GES DISC|LP DAAC)\s+(?:should|must|needs? to)\b",
    r"\b(?:develop|develops|create|creates|build|builds|implement|implements|add|adds|provide|provides)\b",
    r"\brecommend(?:s|ed)? that\b",
)


def _canonicalize_outcome(value: str) -> str:
    outcome = " ".join((value or "").split()).strip()
    if not outcome:
        return ""
    outcome = re.sub(
        r"^(?:Earthdata users|Users|The community)\s+need(?:s)?(?:\s+to)?\s+",
        "",
        outcome,
        flags=re.IGNORECASE,
    )
    outcome = outcome[0].lower() + outcome[1:] if outcome else outcome
    result = f"Earthdata users need {outcome}".strip()
    if not result.endswith((".", "?", "!")):
        result += "."
    return result


def _rewrite_implementation_request(statement: str) -> str:
    suggestion = statement

    # Convert recommendation language into an Earthdata-wide outcome statement.
    suggestion = re.sub(
        r"^Earthdata users need recommend(?:s|ed)? that\s+",
        "Earthdata users need ",
        suggestion,
        flags=re.IGNORECASE,
    )
    suggestion = re.sub(
        r"^Earthdata users need (?:ESDIS|NASA|ASDC|GES DISC|LP DAAC|the DAAC)\s+"
        r"(?:should|must|needs? to|to)?\s*"
        r"(?:develop|develops|create|creates|build|builds|implement|implements|add|adds|provide|provides)\s+",
        "Earthdata users need ",
        suggestion,
        flags=re.IGNORECASE,
    )

    # Common source phrasing: a requested white paper is usually evidence of a
    # need for a clear definition, vision, or operating model—not the paper itself.
    suggestion = re.sub(
        r"^Earthdata users need a short white paper defining and describing the vision for\s+",
        "Earthdata users need a clear, documented vision for ",
        suggestion,
        flags=re.IGNORECASE,
    )
    suggestion = re.sub(
        r"^Earthdata users need a white paper (?:that )?(?:defines|defining|describes|describing)\s+",
        "Earthdata users need a clear, documented definition of ",
        suggestion,
        flags=re.IGNORECASE,
    )

    # Convert imperative implementation verbs into outcome-oriented nouns where
    # the transformation is sufficiently clear and conservative.
    replacements = (
        (r"^Earthdata users need to improve\s+", "Earthdata users need improved "),
        (r"^Earthdata users need to clarify\s+", "Earthdata users need clear "),
        (r"^Earthdata users need to define\s+", "Earthdata users need a clear definition of "),
        (r"^Earthdata users need to document\s+", "Earthdata users need clear documentation of "),
    )
    for pattern, replacement in replacements:
        suggestion = re.sub(pattern, replacement, suggestion, flags=re.IGNORECASE)

    return re.sub(r"\s+", " ", suggestion).strip()


def _recommend(statement: str, desired_outcome: str = "") -> tuple[str, list[str]]:
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

    implementation_language = any(
        re.search(pattern, current, flags=re.IGNORECASE)
        for pattern in IMPLEMENTATION_PATTERNS
    )
    if implementation_language:
        reasons.append("Contains implementation- or organization-specific language")
        rewritten = _rewrite_implementation_request(suggestion)
        if rewritten != suggestion:
            suggestion = rewritten

    if len(current) > 280:
        reasons.append("Canonical statement is unusually long")
    if current.count(".") > 1 or ";" in current:
        reasons.append("May contain multiple outcomes")
    if not current.endswith((".", "?", "!")) and current:
        suggestion += "."
        reasons.append("Missing terminal punctuation")

    suggestion = re.sub(r"\s+", " ", suggestion).strip()

    # When a curated desired outcome already exists, it is a better starting
    # point than returning unchanged implementation language.
    if suggestion.casefold() == current.casefold() and desired_outcome:
        outcome_suggestion = _canonicalize_outcome(desired_outcome)
        if outcome_suggestion and outcome_suggestion.casefold() != current.casefold():
            suggestion = outcome_suggestion
            reasons.append("Recommendation derived from the curated desired outcome")

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
        recommendation, reasons = _recommend(
            row['canonical_need'],
            row.get('desired_outcome') or '',
        )
        if not reasons:
            continue
        if issue and not any(issue.lower() in reason.lower() for reason in reasons):
            continue
        item = dict(row)
        item['recommended_canonical_need'] = recommendation
        item['recommendation_reasons'] = reasons
        item['recommendation_count'] = len(reasons)
        item['changed'] = recommendation.casefold() != row['canonical_need'].casefold()
        item['manual_rewrite_required'] = not item['changed']
        recommendations.append(item)
    return recommendations


@app.get('/curation/needs/recommendations/summary')
def need_recommendation_summary():
    with engine.connect() as connection:
        rows = connection.execute(text('''
            SELECT need_code, canonical_need, desired_outcome FROM needs
        ''')).mappings().all()

    flagged = 0
    actionable = 0
    manual = 0
    grammar = 0
    implementation = 0
    multi_outcome = 0
    for row in rows:
        recommendation, reasons = _recommend(
            row['canonical_need'],
            row.get('desired_outcome') or '',
        )
        if reasons:
            flagged += 1
            if recommendation.casefold() != row['canonical_need'].casefold():
                actionable += 1
            else:
                manual += 1
        grammar += int(any('Grammar' in reason or 'format' in reason or 'punctuation' in reason for reason in reasons))
        implementation += int(any('implementation' in reason for reason in reasons))
        multi_outcome += int(any('multiple outcomes' in reason for reason in reasons))
    return {
        'total_needs': len(rows),
        'flagged_needs': flagged,
        'actionable_recommendations': actionable,
        'manual_rewrite_required': manual,
        'grammar_or_format': grammar,
        'implementation_language': implementation,
        'possible_multiple_outcomes': multi_outcome,
    }
