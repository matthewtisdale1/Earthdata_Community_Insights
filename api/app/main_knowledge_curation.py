import json

from fastapi import HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text

from app.main_review_workspace import app, engine


class CapabilityLinkAction(BaseModel):
    reviewer: str = 'local-curator'
    relationship_type: str = 'Requires'
    confidence: float | None = None
    notes: str | None = None


@app.get('/curation/capabilities/search')
def search_capabilities(
    q: str = '',
    need_code: str = '',
    limit: int = Query(50, ge=1, le=200),
):
    search = (q or '').strip()
    params = {
        'search': f'%{search}%',
        'need_code': need_code,
        'limit': limit,
    }

    with engine.connect() as connection:
        rows = connection.execute(text('''
            SELECT
                c.capability_code,
                c.capability_name,
                c.category,
                c.description,
                c.maturity,
                CASE WHEN nc.need_id IS NULL THEN 0 ELSE 1 END AS linked_to_current_need,
                nc.relationship_type,
                nc.confidence,
                nc.review_status,
                nc.reviewer,
                nc.review_notes
            FROM capabilities c
            LEFT JOIN needs n ON n.need_code = :need_code
            LEFT JOIN need_capabilities nc
              ON nc.need_id = n.need_id
             AND nc.capability_id = c.capability_id
            WHERE c.active = TRUE
              AND (
                    :search = '%%'
                 OR c.capability_code LIKE :search
                 OR c.capability_name LIKE :search
                 OR c.category LIKE :search
                 OR c.description LIKE :search
              )
            ORDER BY linked_to_current_need ASC, c.category, c.capability_name
            LIMIT :limit
        '''), params).mappings().all()

    return [dict(row) for row in rows]


@app.post('/curation/needs/{need_code}/capabilities/{capability_code}/link')
def link_capability_to_need(
    need_code: str,
    capability_code: str,
    action: CapabilityLinkAction,
):
    reviewer = (action.reviewer or '').strip() or 'local-curator'
    relationship_type = (action.relationship_type or 'Requires').strip()
    allowed_relationships = {'Requires', 'Supports', 'Related'}
    if relationship_type not in allowed_relationships:
        raise HTTPException(status_code=400, detail='Invalid capability relationship type')

    confidence = action.confidence
    if confidence is not None and not 0 <= confidence <= 1:
        raise HTTPException(status_code=400, detail='Confidence must be between 0 and 1')

    with engine.begin() as connection:
        need = connection.execute(
            text('SELECT need_id FROM needs WHERE need_code = :code'),
            {'code': need_code},
        ).mappings().first()
        capability = connection.execute(
            text('SELECT capability_id, capability_name FROM capabilities WHERE capability_code = :code AND active = TRUE'),
            {'code': capability_code},
        ).mappings().first()
        if not need:
            raise HTTPException(status_code=404, detail='Canonical need not found')
        if not capability:
            raise HTTPException(status_code=404, detail='Capability not found')

        previous = connection.execute(text('''
            SELECT relationship_type, confidence, review_status, reviewer, review_notes
            FROM need_capabilities
            WHERE need_id = :need_id AND capability_id = :capability_id
        '''), {
            'need_id': need['need_id'],
            'capability_id': capability['capability_id'],
        }).mappings().first()

        connection.execute(text('''
            INSERT INTO need_capabilities (
                need_id, capability_id, relationship_type, confidence,
                match_method, review_status, reviewer, review_notes
            ) VALUES (
                :need_id, :capability_id, :relationship_type, :confidence,
                'Manual curator review', 'Confirmed', :reviewer, :notes
            )
            ON DUPLICATE KEY UPDATE
                relationship_type = VALUES(relationship_type),
                confidence = VALUES(confidence),
                match_method = 'Manual curator review',
                review_status = 'Confirmed',
                reviewer = VALUES(reviewer),
                review_notes = VALUES(review_notes),
                updated_at = NOW()
        '''), {
            'need_id': need['need_id'],
            'capability_id': capability['capability_id'],
            'relationship_type': relationship_type,
            'confidence': confidence,
            'reviewer': reviewer,
            'notes': action.notes,
        })

        connection.execute(text('''
            INSERT INTO review_decisions (
                entity_type, entity_key, decision_type,
                previous_value, new_value, reviewer, review_notes
            ) VALUES (
                'NeedCapability', :entity_key, :decision_type,
                :previous_value, :new_value, :reviewer, :review_notes
            )
        '''), {
            'entity_key': f'{need_code}:{capability_code}',
            'decision_type': 'UpdateLink' if previous else 'Link',
            'previous_value': json.dumps(dict(previous), default=str) if previous else None,
            'new_value': json.dumps({
                'need_code': need_code,
                'capability_code': capability_code,
                'capability_name': capability['capability_name'],
                'relationship_type': relationship_type,
                'confidence': confidence,
                'review_status': 'Confirmed',
            }),
            'reviewer': reviewer,
            'review_notes': action.notes,
        })

    return {
        'linked': True,
        'need_code': need_code,
        'capability_code': capability_code,
        'relationship_type': relationship_type,
    }


@app.post('/curation/needs/{need_code}/capabilities/{capability_code}/unlink')
def unlink_capability_from_need(
    need_code: str,
    capability_code: str,
    action: CapabilityLinkAction,
):
    reviewer = (action.reviewer or '').strip() or 'local-curator'

    with engine.begin() as connection:
        row = connection.execute(text('''
            SELECT n.need_id, c.capability_id, c.capability_name,
                   nc.relationship_type, nc.confidence, nc.review_status,
                   nc.reviewer, nc.review_notes
            FROM need_capabilities nc
            JOIN needs n ON n.need_id = nc.need_id
            JOIN capabilities c ON c.capability_id = nc.capability_id
            WHERE n.need_code = :need_code
              AND c.capability_code = :capability_code
        '''), {
            'need_code': need_code,
            'capability_code': capability_code,
        }).mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail='Capability relationship not found')

        connection.execute(text('''
            DELETE FROM need_capabilities
            WHERE need_id = :need_id AND capability_id = :capability_id
        '''), {
            'need_id': row['need_id'],
            'capability_id': row['capability_id'],
        })

        connection.execute(text('''
            INSERT INTO review_decisions (
                entity_type, entity_key, decision_type,
                previous_value, reviewer, review_notes
            ) VALUES (
                'NeedCapability', :entity_key, 'Unlink',
                :previous_value, :reviewer, :review_notes
            )
        '''), {
            'entity_key': f'{need_code}:{capability_code}',
            'previous_value': json.dumps({
                'need_code': need_code,
                'capability_code': capability_code,
                'capability_name': row['capability_name'],
                'relationship_type': row['relationship_type'],
                'confidence': row['confidence'],
                'review_status': row['review_status'],
                'reviewer': row['reviewer'],
                'review_notes': row['review_notes'],
            }, default=str),
            'reviewer': reviewer,
            'review_notes': action.notes,
        })

    return {
        'linked': False,
        'need_code': need_code,
        'capability_code': capability_code,
    }
