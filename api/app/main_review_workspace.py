import json

from fastapi import HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text

from app.main_knowledge_quality import app, engine, _quality_issues, _score


class EvidenceLinkAction(BaseModel):
    reviewer: str = 'local-reviewer'
    notes: str | None = None


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
                s.source_title,
                enl.review_status AS link_review_status,
                enl.reviewer AS link_reviewer,
                enl.reviewed_at AS link_reviewed_at,
                enl.mapping_method,
                enl.confidence AS link_confidence,
                enl.notes AS link_notes
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


@app.get('/curation/review/evidence/search')
def search_review_evidence(
    q: str,
    need_code: str = '',
    limit: int = Query(50, ge=1, le=200),
):
    search = (q or '').strip()
    if len(search) < 2:
        return []

    with engine.connect() as connection:
        rows = connection.execute(text('''
            SELECT
                e.evidence_code,
                e.original_statement,
                e.evidence_type,
                e.event_year,
                e.user_community,
                e.source_location,
                COALESCE(e.originating_organization_name, o.organization_name) AS originating_organization,
                s.source_title,
                GROUP_CONCAT(DISTINCT CASE
                    WHEN enl.relationship_type = 'Supports' THEN n.need_code
                    ELSE NULL
                END ORDER BY n.need_code SEPARATOR ', ') AS linked_need_codes,
                MAX(CASE WHEN n.need_code = :need_code AND enl.relationship_type = 'Supports' THEN 1 ELSE 0 END) AS linked_to_current_need
            FROM evidence e
            LEFT JOIN organizations o ON o.organization_id = e.organization_id
            LEFT JOIN sources s ON s.source_id = e.source_id
            LEFT JOIN evidence_need_links enl ON enl.evidence_id = e.evidence_id
            LEFT JOIN needs n ON n.need_id = enl.need_id
            WHERE e.duplicate_evidence = FALSE
              AND (
                    e.evidence_code LIKE :search
                 OR e.original_statement LIKE :search
                 OR e.normalized_statement LIKE :search
                 OR e.user_community LIKE :search
                 OR COALESCE(e.originating_organization_name, o.organization_name) LIKE :search
                 OR s.source_title LIKE :search
              )
            GROUP BY e.evidence_id, e.evidence_code, e.original_statement,
                     e.evidence_type, e.event_year, e.user_community,
                     e.source_location,
                     COALESCE(e.originating_organization_name, o.organization_name),
                     s.source_title
            ORDER BY linked_to_current_need ASC, e.event_year DESC, e.evidence_code
            LIMIT :limit
        '''), {
            'search': f'%{search}%',
            'need_code': need_code,
            'limit': limit,
        }).mappings().all()
    return [dict(row) for row in rows]


@app.post('/curation/review/needs/{need_code}/evidence/{evidence_code}/link')
def link_evidence_to_need(
    need_code: str,
    evidence_code: str,
    action: EvidenceLinkAction,
):
    reviewer = (action.reviewer or '').strip() or 'local-reviewer'
    with engine.begin() as connection:
        need = connection.execute(
            text('SELECT need_id FROM needs WHERE need_code = :code'),
            {'code': need_code},
        ).mappings().first()
        evidence = connection.execute(
            text('SELECT evidence_id, need_id FROM evidence WHERE evidence_code = :code AND duplicate_evidence = FALSE'),
            {'code': evidence_code},
        ).mappings().first()
        if not need:
            raise HTTPException(status_code=404, detail='Canonical need not found')
        if not evidence:
            raise HTTPException(status_code=404, detail='Evidence not found')

        connection.execute(text('''
            INSERT INTO evidence_need_links (
                evidence_id, need_id, relationship_type, mapping_method,
                review_status, reviewer, reviewed_at, notes
            ) VALUES (
                :evidence_id, :need_id, 'Supports', 'Manual curator review',
                'Confirmed', :reviewer, NOW(), :notes
            )
            ON DUPLICATE KEY UPDATE
                mapping_method = 'Manual curator review',
                review_status = 'Confirmed',
                reviewer = VALUES(reviewer),
                reviewed_at = NOW(),
                notes = VALUES(notes),
                updated_at = NOW()
        '''), {
            'evidence_id': evidence['evidence_id'],
            'need_id': need['need_id'],
            'reviewer': reviewer,
            'notes': action.notes,
        })

        # Keep the legacy one-to-many pointer usable without overwriting an
        # existing primary association. The many-to-many link table is authoritative.
        if evidence['need_id'] is None:
            connection.execute(
                text('UPDATE evidence SET need_id = :need_id WHERE evidence_id = :evidence_id'),
                {'need_id': need['need_id'], 'evidence_id': evidence['evidence_id']},
            )

        connection.execute(text('''
            INSERT INTO review_decisions (
                entity_type, entity_key, decision_type, new_value,
                reviewer, review_notes
            ) VALUES (
                'EvidenceNeedLink', :entity_key, 'Link', :new_value,
                :reviewer, :review_notes
            )
        '''), {
            'entity_key': f'{need_code}:{evidence_code}',
            'new_value': json.dumps({
                'need_code': need_code,
                'evidence_code': evidence_code,
                'relationship_type': 'Supports',
                'review_status': 'Confirmed',
            }),
            'reviewer': reviewer,
            'review_notes': action.notes,
        })
    return {'linked': True, 'need_code': need_code, 'evidence_code': evidence_code}


@app.post('/curation/review/needs/{need_code}/evidence/{evidence_code}/unlink')
def unlink_evidence_from_need(
    need_code: str,
    evidence_code: str,
    action: EvidenceLinkAction,
):
    reviewer = (action.reviewer or '').strip() or 'local-reviewer'
    with engine.begin() as connection:
        row = connection.execute(text('''
            SELECT enl.evidence_need_link_id, e.evidence_id, e.need_id,
                   n.need_id AS target_need_id
            FROM evidence_need_links enl
            JOIN evidence e ON e.evidence_id = enl.evidence_id
            JOIN needs n ON n.need_id = enl.need_id
            WHERE n.need_code = :need_code
              AND e.evidence_code = :evidence_code
              AND enl.relationship_type = 'Supports'
        '''), {
            'need_code': need_code,
            'evidence_code': evidence_code,
        }).mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail='Supporting evidence link not found')

        connection.execute(
            text('DELETE FROM evidence_need_links WHERE evidence_need_link_id = :link_id'),
            {'link_id': row['evidence_need_link_id']},
        )

        # If the removed relationship was also the legacy primary pointer,
        # point it at another remaining Supports relationship when available.
        if row['need_id'] == row['target_need_id']:
            replacement = connection.execute(text('''
                SELECT need_id
                FROM evidence_need_links
                WHERE evidence_id = :evidence_id
                  AND relationship_type = 'Supports'
                ORDER BY review_status = 'Confirmed' DESC, evidence_need_link_id
                LIMIT 1
            '''), {'evidence_id': row['evidence_id']}).scalar()
            connection.execute(text('''
                UPDATE evidence SET need_id = :replacement
                WHERE evidence_id = :evidence_id
            '''), {
                'replacement': replacement,
                'evidence_id': row['evidence_id'],
            })

        connection.execute(text('''
            INSERT INTO review_decisions (
                entity_type, entity_key, decision_type, previous_value,
                reviewer, review_notes
            ) VALUES (
                'EvidenceNeedLink', :entity_key, 'Unlink', :previous_value,
                :reviewer, :review_notes
            )
        '''), {
            'entity_key': f'{need_code}:{evidence_code}',
            'previous_value': json.dumps({
                'need_code': need_code,
                'evidence_code': evidence_code,
                'relationship_type': 'Supports',
            }),
            'reviewer': reviewer,
            'review_notes': action.notes,
        })
    return {'linked': False, 'need_code': need_code, 'evidence_code': evidence_code}
