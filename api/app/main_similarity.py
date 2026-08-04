import re

from fastapi import HTTPException, Query
from sqlalchemy import text

from app.main_need_history import app, engine

STOPWORDS = {
    'the', 'and', 'for', 'that', 'with', 'from', 'this', 'users', 'user',
    'earthdata', 'need', 'needs', 'should', 'data', 'are', 'was', 'were',
    'have', 'has', 'into', 'more', 'their', 'they', 'using', 'use', 'can'
}


def tokens(value: str) -> set[str]:
    return {
        token for token in re.findall(r"[a-z0-9]+", (value or '').lower())
        if len(token) > 2 and token not in STOPWORDS
    }


def similarity(left: str, right: str) -> float:
    a, b = tokens(left), tokens(right)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


@app.get('/curation/evidence/{evidence_code}/similar')
def similar_evidence(evidence_code: str, limit: int = Query(5, ge=1, le=20)):
    with engine.connect() as connection:
        target = connection.execute(
            text('SELECT original_statement FROM evidence WHERE evidence_code = :code'),
            {'code': evidence_code},
        ).mappings().first()
        if not target:
            raise HTTPException(status_code=404, detail='Evidence not found')
        rows = connection.execute(text('''
            SELECT e.evidence_code, e.original_statement, e.event_year,
                   COALESCE(e.originating_organization_name, o.organization_name) AS originating_organization,
                   s.source_title, n.need_code, n.canonical_need
            FROM evidence e
            LEFT JOIN organizations o ON o.organization_id = e.organization_id
            LEFT JOIN sources s ON s.source_id = e.source_id
            LEFT JOIN evidence_need_links enl ON enl.evidence_id = e.evidence_id AND enl.relationship_type = 'Supports'
            LEFT JOIN needs n ON n.need_id = COALESCE(enl.need_id, e.need_id)
            WHERE e.evidence_code <> :code AND e.duplicate_evidence = FALSE
            ORDER BY e.event_year DESC
            LIMIT 2000
        '''), {'code': evidence_code}).mappings().all()

    ranked = []
    for row in rows:
        record = dict(row)
        score = similarity(target['original_statement'], record['original_statement'])
        if score > 0:
            record['similarity_score'] = round(score, 4)
            record['shared_terms'] = sorted(tokens(target['original_statement']) & tokens(record['original_statement']))
            ranked.append(record)
    ranked.sort(key=lambda item: (-item['similarity_score'], item['evidence_code']))
    return ranked[:limit]
