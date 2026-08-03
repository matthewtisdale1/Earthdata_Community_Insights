from fastapi import HTTPException
from sqlalchemy import text

from app.main import app, engine


@app.get("/tools")
def list_tools():
    with engine.connect() as connection:
        records = connection.execute(
            text(
                """
                SELECT *
                FROM v_tool_summary
                ORDER BY tool_name
                """
            )
        ).mappings().all()

    return [dict(record) for record in records]


@app.get("/tools/{tool_code}")
def get_tool(tool_code: str):
    with engine.connect() as connection:
        tool = connection.execute(
            text(
                """
                SELECT *
                FROM v_tool_summary
                WHERE tool_code = :tool_code
                """
            ),
            {"tool_code": tool_code},
        ).mappings().first()

        if not tool:
            raise HTTPException(
                status_code=404,
                detail="Tool not found",
            )

        sources = connection.execute(
            text(
                """
                SELECT
                    source_code,
                    source_kind,
                    owner_name,
                    repository_name,
                    base_url,
                    api_url,
                    active,
                    sync_enabled,
                    last_synced_at,
                    sync_status,
                    sync_error
                FROM external_sources
                WHERE tool_id = :tool_id
                ORDER BY source_code
                """
            ),
            {"tool_id": tool["tool_id"]},
        ).mappings().all()

        artifact_counts = connection.execute(
            text(
                """
                SELECT
                    artifact_type,
                    state,
                    COUNT(*) AS artifact_count
                FROM implementation_artifacts
                WHERE tool_id = :tool_id
                GROUP BY artifact_type, state
                ORDER BY artifact_type, state
                """
            ),
            {"tool_id": tool["tool_id"]},
        ).mappings().all()

        recent_artifacts = connection.execute(
            text(
                """
                SELECT
                    artifact_code,
                    artifact_type,
                    external_number,
                    title,
                    state,
                    external_url,
                    updated_external_at
                FROM implementation_artifacts
                WHERE tool_id = :tool_id
                ORDER BY updated_external_at DESC
                LIMIT 50
                """
            ),
            {"tool_id": tool["tool_id"]},
        ).mappings().all()

    return {
        "tool": dict(tool),
        "sources": [dict(record) for record in sources],
        "artifact_counts": [dict(record) for record in artifact_counts],
        "recent_artifacts": [dict(record) for record in recent_artifacts],
    }
