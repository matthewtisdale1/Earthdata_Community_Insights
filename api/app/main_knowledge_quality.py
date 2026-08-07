import re
from collections import Counter
from typing import Optional

from fastapi import Query
from sqlalchemy import text

from app.main_similarity import app, engine


IMPLEMENTATION_PATTERNS = (
    r"\b(?:ESDIS|NASA|DAAC|ASDC|GES DISC|LP DAAC)\b",
    r"\b(?:develop|develops|create|creates|build|builds|implement|implements)\b",
    r"\brecommend(?:s|ed)? that\b",
)


def _quality_issues(row: dict) -> list[dict]:
    statement = " ".join((row.get("canonical_need") or "").split())
    issues: list[dict] = []

    if not re.match(r"^Earthdata users need\b", statement, flags=re.IGNORECASE):
        issues.append({"code": "canonical_format", "label": "Nonstandard canonical format", "penalty": 10})

    if not statement.endswith((".", "?", "!")):
        issues.append({"code": "punctuation", "label": "Missing terminal punctuation", "penalty": 2})

    if len(statement) > 280:
        issues.append({"code": "long_statement", "label": "Canonical statement is unusually long", "penalty": 5})

    if statement.count(".") > 1 or ";" in statement:
        issues.append({"code": "multiple_outcomes", "label": "May contain multiple outcomes", "penalty": 10})

    if any(re.search(pattern, statement, flags=re.IGNORECASE) for pattern in IMPLEMENTATION_PATTERNS):
        issues.append({"code": "implementation_language", "label": "Contains implementation- or organization-specific language", "penalty": 10})

    if not (row.get("desired_outcome") or "").strip():
        issues.append({"code": "missing_outcome", "label": "Missing desired outcome", "penalty": 15})

    if not bool(row.get("human_reviewed")):
        issues.append({"code": "not_reviewed", "label": "Canonical need has not been human reviewed", "penalty": 15})

    if int(row.get("capability_count") or 0) == 0:
        issues.append({"code": "missing_capability", "label": "No capability mapping", "penalty": 15})

    if int(row.get("evidence_count") or 0) <= 1:
        issues.append({"code": "low_evidence", "label": "Supported by one or fewer evidence records", "penalty": 10})

    return issues


def _score(issues: list[dict]) -> int:
    return max(0, 100 - sum(int(issue["penalty"]) for issue in issues))


def _load_needs(connection, q: str = "", limit: int = 500):
    conditions = ["1=1"]
    params = {"limit": limit}
    if q:
        conditions.append("(n.need_code LIKE :search OR n.canonical_need LIKE :search)")
        params["search"] = f"%{q}%"

    return connection.execute(text(f"""
        SELECT
            n.need_code,
            n.canonical_need,
            n.need_category,
            n.lifecycle_status,
            n.human_reviewed,
            n.reviewer,
            n.desired_outcome,
            n.notes,
            COALESCE(v.evidence_count, 0) AS evidence_count,
            COALESCE(v.organization_count, 0) AS organization_count,
            COALESCE(v.year_count, 0) AS year_count,
            COUNT(DISTINCT CASE WHEN nc.review_status = 'Confirmed' THEN nc.capability_id END) AS capability_count
        FROM needs n
        LEFT JOIN v_need_summary v ON v.need_id = n.need_id
        LEFT JOIN need_capabilities nc ON nc.need_id = n.need_id
        WHERE {' AND '.join(conditions)}
        GROUP BY
            n.need_id, n.need_code, n.canonical_need, n.need_category,
            n.lifecycle_status, n.human_reviewed, n.reviewer,
            n.desired_outcome, n.notes,
            v.evidence_count, v.organization_count, v.year_count
        ORDER BY n.need_code
        LIMIT :limit
    """), params).mappings().all()


@app.get('/curation/quality/needs')
def need_quality_queue(
    q: str = '',
    issue: str = '',
    max_score: Optional[int] = Query(None, ge=0, le=100),
    limit: int = Query(500, ge=1, le=500),
):
    with engine.connect() as connection:
        rows = _load_needs(connection, q=q, limit=limit)

    results = []
    for row in rows:
        item = dict(row)
        issues = _quality_issues(item)
        score = _score(issues)
        if issue and not any(problem['code'] == issue for problem in issues):
            continue
        if max_score is not None and score > max_score:
            continue
        item['quality_score'] = score
        item['quality_issues'] = issues
        item['issue_count'] = len(issues)
        results.append(item)

    results.sort(key=lambda item: (item['quality_score'], -item['evidence_count'], item['need_code']))
    return results


@app.get('/curation/quality/summary')
def knowledge_quality_summary():
    with engine.connect() as connection:
        rows = _load_needs(connection, limit=500)
        corpus = connection.execute(text('''
            SELECT
                (SELECT COUNT(*) FROM evidence WHERE duplicate_evidence = FALSE) AS evidence_count,
                (SELECT COUNT(*) FROM needs) AS need_count,
                (SELECT COUNT(DISTINCT user_community) FROM evidence WHERE user_community IS NOT NULL AND user_community <> '') AS community_count,
                (SELECT MIN(event_year) FROM evidence WHERE duplicate_evidence = FALSE) AS first_year,
                (SELECT MAX(event_year) FROM evidence WHERE duplicate_evidence = FALSE) AS last_year,
                (SELECT COUNT(*) FROM organizations) AS organization_count
        ''')).mappings().one()

    scores = []
    counter = Counter()
    needs_attention = 0
    reviewed = 0
    for row in rows:
        item = dict(row)
        issues = _quality_issues(item)
        score = _score(issues)
        scores.append(score)
        if issues:
            needs_attention += 1
        if item.get('human_reviewed'):
            reviewed += 1
        counter.update(issue['code'] for issue in issues)

    total = len(rows)
    return {
        'overall_health': round(sum(scores) / total, 1) if total else 100.0,
        'total_needs': total,
        'needs_attention': needs_attention,
        'reviewed_needs': reviewed,
        'reviewed_percent': round((reviewed / total) * 100, 1) if total else 100.0,
        'issue_counts': dict(counter),
        'corpus': dict(corpus),
    }
