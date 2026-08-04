import re
from typing import Optional

from fastapi import Query
from sqlalchemy import text

from app.main_capabilities import app, engine


TERMINAL_PUNCTUATION = ('.', '!', '?')
VAGUE_PHRASES = (
    'better',
    'easier',
    'improve',
    'improved',
    'more user friendly',
    'more useful',
    'and what users can do',
)
SOLUTION_TERMS = (
    'harmony should',
    'earthdata search should',
    'worldview should',
    'cmr should',
    'gibs should',
    'arcgis should',
)


def assess_need(statement: str) -> dict:
    text_value = (statement or '').strip()
    words = re.findall(r"[A-Za-z0-9'-]+", text_value)
    lowered = text_value.lower()
    flags = []

    if not text_value:
        flags.append('Empty statement')
    else:
        if len(words) < 6:
            flags.append('Very short statement')
        if len(words) > 45:
            flags.append('Long or multi-part statement')
        if not text_value.endswith(TERMINAL_PUNCTUATION):
            flags.append('Missing terminal punctuation')
        if text_value[:1].islower():
            flags.append('Starts with lowercase text')
        if re.search(r'\b([a-z]+)\s+\1\b', lowered):
            flags.append('Repeated adjacent word')
        if any(phrase in lowered for phrase in VAGUE_PHRASES):
            flags.append('Potentially vague wording')
        if any(term in lowered for term in SOLUTION_TERMS):
            flags.append('May prescribe a specific solution')
        if ' and ' in lowered and len(words) > 22:
            flags.append('May combine multiple needs')
        if not any(
            marker in lowered
            for marker in (' need ', ' needs ', ' require ', ' requires ', ' must ', ' should ', ' ability ', ' access ')
        ):
            flags.append('Outcome or need may be unclear')

    severity = 'Clear'
    if flags:
        severity = 'Review'
    if any(
        flag in flags
        for flag in (
            'Empty statement',
            'Repeated adjacent word',
            'Very short statement',
            'Outcome or need may be unclear',
        )
    ):
        severity = 'High priority'

    return {
        'quality_status': severity,
        'quality_flag_count': len(flags),
        'quality_flags': flags,
    }


@app.get('/quality/needs')
def need_quality_review(
    status: str = '',
    reviewed: Optional[bool] = None,
    limit: int = Query(500, ge=1, le=1000),
):
    conditions = ['1=1']
    parameters = {'limit': limit}

    if reviewed is not None:
        conditions.append('human_reviewed = :reviewed')
        parameters['reviewed'] = reviewed

    with engine.connect() as connection:
        rows = connection.execute(
            text(f'''
                SELECT
                    need_code,
                    canonical_need,
                    need_category,
                    human_reviewed,
                    reviewer,
                    review_date,
                    evidence_count,
                    organization_count,
                    year_count,
                    signal_score
                FROM v_need_summary
                WHERE {' AND '.join(conditions)}
                ORDER BY signal_score DESC, evidence_count DESC, need_code
                LIMIT :limit
            '''),
            parameters,
        ).mappings().all()

    results = []
    for row in rows:
        record = dict(row)
        record.update(assess_need(record.get('canonical_need', '')))
        if status and record['quality_status'].lower() != status.lower():
            continue
        results.append(record)

    results.sort(
        key=lambda item: (
            0 if item['quality_status'] == 'High priority' else 1,
            -item['quality_flag_count'],
            -int(item.get('signal_score') or 0),
            item['need_code'],
        )
    )
    return results
