from typing import Optional

from fastapi import Query
from sqlalchemy import text

from app.main_capabilities import app, engine


@app.get('/curation/evidence/summary')
def evidence_queue_summary():
    with engine.connect() as connection:
        row = connection.execute(text('''
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN human_reviewed = FALSE THEN 1 ELSE 0 END) AS unreviewed,
                SUM(CASE WHEN human_reviewed = TRUE THEN 1 ELSE 0 END) AS reviewed,
                COUNT(DISTINCT source_id) AS source_count,
                COUNT(DISTINCT event_year) AS year_count
            FROM evidence
            WHERE duplicate_evidence = FALSE
        ''')).mappings().one()
    return dict(row)


@app.get('/curation/evidence')
def evidence_queue(
    q: str = '',
    reviewed: Optional[bool] = None,
    source_code: str = '',
    organization: str = '',
    year: Optional[int] = None,
    limit: int = Query(500, ge=1, le=1000),
):
    conditions = ['e.duplicate_evidence = FALSE']
    parameters = {'limit': limit}
    if q:
        conditions.append('(e.original_statement LIKE :search OR e.evidence_code LIKE :search OR n.canonical_need LIKE :search)')
        parameters['search'] = f'%{q}%'
    if reviewed is not None:
        conditions.append('e.human_reviewed = :reviewed')
        parameters['reviewed'] = reviewed
    if source_code:
        conditions.append('s.source_code = :source_code')
        parameters['source_code'] = source_code
    if organization:
        conditions.append('o.organization_name = :organization')
        parameters['organization'] = organization
    if year is not None:
        conditions.append('e.event_year = :year')
        parameters['year'] = year

    with engine.connect() as connection:
        rows = connection.execute(text(f'''
            SELECT
                e.evidence_code,
                e.original_statement,
                e.evidence_type,
                e.event_year,
                e.human_reviewed,
                e.source_section,
                e.source_page,
                COALESCE(e.originating_organization_name, o.organization_name) AS originating_organization,
                s.source_code,
                s.source_title,
                n.need_code,
                n.canonical_need,
                COALESCE(enl.review_status,
                    CASE WHEN e.human_reviewed THEN 'Confirmed' ELSE 'Candidate' END
                ) AS review_status
            FROM evidence e
            LEFT JOIN evidence_need_links enl
              ON enl.evidence_id = e.evidence_id
             AND enl.relationship_type = 'Supports'
            LEFT JOIN needs n
              ON n.need_id = COALESCE(enl.need_id, e.need_id)
            LEFT JOIN sources s ON s.source_id = e.source_id
            LEFT JOIN organizations o ON o.organization_id = e.organization_id
            WHERE {' AND '.join(conditions)}
            ORDER BY e.human_reviewed, e.event_year DESC, e.evidence_code
            LIMIT :limit
        '''), parameters).mappings().all()
    return [dict(row) for row in rows]
