from fastapi import HTTPException, Query
from sqlalchemy import text

from app.main_curation import app, engine


@app.get('/curation/needs/{need_code}/history')
def need_review_history(need_code: str, limit: int = Query(100, ge=1, le=500)):
    with engine.connect() as connection:
        exists = connection.execute(
            text('SELECT 1 FROM needs WHERE need_code = :code'),
            {'code': need_code},
        ).first()
        if not exists:
            raise HTTPException(status_code=404, detail='Canonical need not found')
        rows = connection.execute(text('''
            SELECT review_id, decision_type, previous_value, new_value,
                   reviewer, review_notes, reviewed_at
            FROM review_decisions
            WHERE entity_type = 'Need' AND entity_key = :code
            ORDER BY reviewed_at DESC, review_id DESC
            LIMIT :limit
        '''), {'code': need_code, 'limit': limit}).mappings().all()
    return [dict(row) for row in rows]


@app.get('/curation/needs/{need_code}/evidence-summary')
def need_evidence_summary(need_code: str):
    with engine.connect() as connection:
        row = connection.execute(text('''
            SELECT n.need_code, n.canonical_need,
                   COUNT(DISTINCT enl.evidence_id) AS evidence_count,
                   COUNT(DISTINCT e.source_id) AS source_count,
                   COUNT(DISTINCT COALESCE(e.originating_organization_name, o.organization_name)) AS originating_organization_count,
                   COUNT(DISTINCT e.event_year) AS year_count,
                   MIN(e.event_year) AS first_seen_year,
                   MAX(e.event_year) AS last_seen_year
            FROM needs n
            LEFT JOIN evidence_need_links enl ON enl.need_id = n.need_id
            LEFT JOIN evidence e ON e.evidence_id = enl.evidence_id AND e.duplicate_evidence = FALSE
            LEFT JOIN organizations o ON o.organization_id = e.organization_id
            WHERE n.need_code = :code
            GROUP BY n.need_id, n.need_code, n.canonical_need
        '''), {'code': need_code}).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail='Canonical need not found')
    return dict(row)
