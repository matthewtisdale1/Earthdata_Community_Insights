from fastapi import HTTPException
from sqlalchemy import text

from app.main_context import app, engine


@app.get('/capabilities')
def list_capabilities():
    with engine.connect() as connection:
        rows = connection.execute(text('''
            SELECT * FROM v_capability_summary
            WHERE active = TRUE
            ORDER BY need_count DESC, capability_name
        ''')).mappings().all()
    return [dict(row) for row in rows]


@app.get('/capabilities/{capability_code}')
def get_capability(capability_code: str):
    with engine.connect() as connection:
        capability = connection.execute(text('''
            SELECT * FROM v_capability_summary
            WHERE capability_code = :code
        '''), {'code': capability_code}).mappings().first()
        if not capability:
            raise HTTPException(status_code=404, detail='Capability not found')

        tools = connection.execute(text('''
            SELECT t.tool_code, t.tool_name, tc.support_level,
                   tc.evidence_source, tc.notes, tc.reviewed
            FROM tool_capabilities tc
            JOIN tools t ON t.tool_id = tc.tool_id
            JOIN capabilities c ON c.capability_id = tc.capability_id
            WHERE c.capability_code = :code
            ORDER BY t.tool_name
        '''), {'code': capability_code}).mappings().all()

        needs = connection.execute(text('''
            SELECT n.need_code, n.canonical_need, n.need_category,
                   nc.relationship_type, nc.confidence, nc.review_status,
                   COUNT(DISTINCT e.evidence_id) AS evidence_count,
                   COUNT(DISTINCT e.organization_id) AS organization_count
            FROM need_capabilities nc
            JOIN needs n ON n.need_id = nc.need_id
            JOIN capabilities c ON c.capability_id = nc.capability_id
            LEFT JOIN evidence e ON e.need_id = n.need_id
            WHERE c.capability_code = :code
            GROUP BY n.need_id, n.need_code, n.canonical_need, n.need_category,
                     nc.relationship_type, nc.confidence, nc.review_status
            ORDER BY nc.review_status='Confirmed' DESC, evidence_count DESC
        '''), {'code': capability_code}).mappings().all()

        artifacts = connection.execute(text('''
            SELECT DISTINCT ia.artifact_code, ia.artifact_type,
                   ia.external_number, ia.title, ia.state, ia.external_url,
                   t.tool_code, t.tool_name, nam.review_status,
                   nam.relationship_type, nam.overall_score
            FROM need_capabilities nc
            JOIN need_artifact_matches nam ON nam.need_id = nc.need_id
            JOIN implementation_artifacts ia ON ia.artifact_id = nam.artifact_id
            JOIN tools t ON t.tool_id = ia.tool_id
            JOIN capabilities c ON c.capability_id = nc.capability_id
            WHERE c.capability_code = :code
            ORDER BY nam.review_status='Confirmed' DESC, nam.overall_score DESC
            LIMIT 100
        '''), {'code': capability_code}).mappings().all()

    return {
        'capability': dict(capability),
        'tools': [dict(row) for row in tools],
        'needs': [dict(row) for row in needs],
        'artifacts': [dict(row) for row in artifacts],
    }


@app.get('/tools/{tool_code}/capabilities')
def tool_capabilities(tool_code: str):
    with engine.connect() as connection:
        rows = connection.execute(text('''
            SELECT c.capability_code, c.capability_name, c.category,
                   c.description, tc.support_level, tc.reviewed
            FROM tool_capabilities tc
            JOIN tools t ON t.tool_id = tc.tool_id
            JOIN capabilities c ON c.capability_id = tc.capability_id
            WHERE t.tool_code = :tool_code
            ORDER BY c.category, c.capability_name
        '''), {'tool_code': tool_code}).mappings().all()
    return [dict(row) for row in rows]


@app.get('/needs/{need_code}/capabilities')
def need_capabilities(need_code: str):
    with engine.connect() as connection:
        rows = connection.execute(text('''
            SELECT c.capability_code, c.capability_name, c.category,
                   c.description, nc.relationship_type, nc.confidence,
                   nc.review_status, nc.match_method
            FROM need_capabilities nc
            JOIN needs n ON n.need_id = nc.need_id
            JOIN capabilities c ON c.capability_id = nc.capability_id
            WHERE n.need_code = :need_code
            ORDER BY nc.review_status='Confirmed' DESC, nc.confidence DESC
        '''), {'need_code': need_code}).mappings().all()
    return [dict(row) for row in rows]
