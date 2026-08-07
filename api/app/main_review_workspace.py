from fastapi import HTTPException, Query
from sqlalchemy import text

from app.main_knowledge_quality import app, engine, _quality_issues, _score


@app.get('/curation/review/options')
def review_options():
    with engine.connect() as connection:
        organizations = connection.execute(text('''
            SELECT DISTINCT COALESCE(e.originating_organization_name, o.organization_name) AS value
            FROM evidence e
            LEFT JOIN organizations o ON o.organization_id = e.organization_id
            WHERE COALESCE(e.originating_organization_name, o.organization_name) IS NOT NULL
              AND COALESCE(e.originating_organization_name, o.organization_name) <> ''
            ORDER BY value
        ''')).scalars().all()
        communities = connection.execute(text('''
            SELECT DISTINCT user_community
            FROM evidence
            WHERE user_community IS NOT NULL AND user_community <> ''
            ORDER BY user_community
        ''')).scalars().all()
    return {
        'organizations': organizations,
        'communities': communities,
    }


@app.get('/curation/review/needs')
def review_need_queue(
    q: str = '',
    organization: str = '',
    community: str = '',
    reviewed: str = '',
    limit: int = Query(500, ge=1, le=500),
):
    conditions = ['1=1']
    params = {'limit': limit}

    if q:
        conditions.append('(n.need_code LIKE :search OR n.canonical_need LIKE :search)')
        params['search'] = f'%{q}%'
    if organization:
        conditions.append('COALESCE(e.originating_organization_name, o.organization_name) = :organization')
        params['organization'] = organization
    if community:
        conditions.append('e.user_community = :community')
        params['community'] = community
    if reviewed == 'reviewed':
        conditions.append('n.human_reviewed = TRUE')
    elif reviewed == 'unreviewed':
        conditions.append('n.human_reviewed = FALSE')

    with engine.connect() as connection:
        rows = connection.execute(text(f'''
            SELECT
                n.need_code,
                n.canonical_need,
                n.need_category,
                n.lifecycle_status,
                n.human_reviewed,
                n.reviewer,
                n.review_date,
                COUNT(DISTINCT e.evidence_id) AS evidence_count,
                COUNT(DISTINCT e.event_year) AS year_count,
                MIN(e.event_year) AS first_seen_year,
                MAX(e.event_year) AS last_seen_year,
                COUNT(DISTINCT COALESCE(e.originating_organization_name, o.organization_name)) AS organization_count,
                COUNT(DISTINCT CASE WHEN nc.review_status = 'Confirmed' THEN nc.capability_id END) AS capability_count
            FROM needs n
            LEFT JOIN evidence_need_links enl ON enl.need_id = n.need_id AND enl.relationship_type = 'Supports'
            LEFT JOIN evidence e ON e.evidence_id = enl.evidence_id AND e.duplicate_evidence = FALSE
            LEFT JOIN organizations o ON o.organization_id = e.organization_id
            LEFT JOIN need_capabilities nc ON nc.need_id = n.need_id
            WHERE {' AND '.join(conditions)}
            GROUP BY n.need_id, n.need_code, n.canonical_need, n.need_category,
                     n.lifecycle_status, n.human_reviewed, n.reviewer, n.review_date
            ORDER BY n.human_reviewed, evidence_count DESC, n.need_code
            LIMIT :limit
        '''), params).mappings().all()

    return [dict(row) for row in rows]


@app.get('/curation/review/needs/{need_code}')
def review_need_detail(need_code: str):
    with engine.connect() as connection:
        need = connection.execute(text('''
            SELECT n.*,
                   COALESCE(v.evidence_count, 0) AS evidence_count,
                   COALESCE(v.organization_count, 0) AS organization_count,
                   COALESCE(v.year_count, 0) AS year_count
            FROM needs n
            LEFT JOIN v_need_summary v ON v.need_id = n.need_id
            WHERE n.need_code = :code
        '''), {'code': need_code}).mappings().first()
        if not need:
            raise HTTPException(status_code=404, detail='Canonical need not found')

        evidence = connection.execute(text('''
            SELECT DISTINCT
                e.evidence_code,
                e.original_statement,
                e.normalized_statement,
                e.evidence_type,
                e.event_year,
                e.user_community,
                e.source_location,
                e.human_reviewed,
                COALESCE(e.originating_organization_name, o.organization_name) AS originating_organization,
                s.source_code,
                s.source_title
            FROM needs n
            JOIN evidence_need_links enl ON enl.need_id = n.need_id AND enl.relationship_type = 'Supports'
            JOIN evidence e ON e.evidence_id = enl.evidence_id AND e.duplicate_evidence = FALSE
            LEFT JOIN organizations o ON o.organization_id = e.organization_id
            LEFT JOIN sources s ON s.source_id = e.source_id
            WHERE n.need_code = :code
            ORDER BY e.event_year DESC, e.evidence_code
        '''), {'code': need_code}).mappings().all()

        capabilities = connection.execute(text('''
            SELECT c.capability_code, c.capability_name, c.category,
                   nc.relationship_type, nc.confidence, nc.review_status, nc.match_method
            FROM need_capabilities nc
            JOIN needs n ON n.need_id = nc.need_id
            JOIN capabilities c ON c.capability_id = nc.capability_id
            WHERE n.need_code = :code
            ORDER BY nc.review_status = 'Confirmed' DESC, nc.confidence DESC, c.capability_name
        '''), {'code': need_code}).mappings().all()

        history = connection.execute(text('''
            SELECT review_id, decision_type, previous_value, new_value,
                   reviewer, review_notes, reviewed_at
            FROM review_decisions
            WHERE entity_type = 'Need' AND entity_key = :code
            ORDER BY reviewed_at DESC, review_id DESC
            LIMIT 50
        '''), {'code': need_code}).mappings().all()

        origins = connection.execute(text('''
            SELECT
                COALESCE(e.originating_organization_name, o.organization_name) AS organization,
                COUNT(DISTINCT e.evidence_id) AS evidence_count,
                MIN(e.event_year) AS first_year,
                MAX(e.event_year) AS last_year
            FROM needs n
            JOIN evidence_need_links enl ON enl.need_id = n.need_id AND enl.relationship_type = 'Supports'
            JOIN evidence e ON e.evidence_id = enl.evidence_id AND e.duplicate_evidence = FALSE
            LEFT JOIN organizations o ON o.organization_id = e.organization_id
            WHERE n.need_code = :code
            GROUP BY COALESCE(e.originating_organization_name, o.organization_name)
            ORDER BY evidence_count DESC, organization
        '''), {'code': need_code}).mappings().all()

    item = dict(need)
    item['capability_count'] = sum(1 for row in capabilities if row['review_status'] == 'Confirmed')
    issues = _quality_issues(item)
    return {
        'need': item,
        'quality_score': _score(issues),
        'quality_issues': issues,
        'evidence': [dict(row) for row in evidence],
        'capabilities': [dict(row) for row in capabilities],
        'history': [dict(row) for row in history],
        'origins': [dict(row) for row in origins],
    }
