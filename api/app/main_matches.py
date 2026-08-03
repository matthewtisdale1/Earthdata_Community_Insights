from typing import Optional

from fastapi import HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text

from app.main_tools import app, engine


class MatchReviewUpdate(BaseModel):
    relationship_type: str
    review_status: str
    reviewer: str
    review_notes: Optional[str] = None


@app.get("/matches/pending")
def list_pending_matches(
    minimum_score: float = 0.0,
    tool_code: str = "",
    limit: int = Query(250, ge=1, le=1000),
):
    conditions = ["nam.review_status = 'Pending'", "nam.overall_score >= :minimum_score"]
    parameters = {"minimum_score": minimum_score, "limit": limit}
    if tool_code:
        conditions.append("t.tool_code = :tool_code")
        parameters["tool_code"] = tool_code

    query = f"""
        SELECT nam.match_id, nam.relationship_type, nam.lexical_score,
               nam.overall_score, nam.matched_terms, nam.match_explanation,
               n.need_code, n.canonical_need, n.need_category,
               ia.artifact_code, ia.artifact_type, ia.external_number,
               ia.title, ia.state, ia.external_url,
               t.tool_code, t.tool_name,
               es.owner_name, es.repository_name
        FROM need_artifact_matches nam
        JOIN needs n ON n.need_id = nam.need_id
        JOIN implementation_artifacts ia ON ia.artifact_id = nam.artifact_id
        JOIN tools t ON t.tool_id = ia.tool_id
        JOIN external_sources es ON es.external_source_id = ia.external_source_id
        WHERE {' AND '.join(conditions)}
        ORDER BY nam.overall_score DESC, n.need_code
        LIMIT :limit
    """
    with engine.connect() as connection:
        records = connection.execute(text(query), parameters).mappings().all()
    return [dict(record) for record in records]


@app.patch("/matches/{match_id}")
def review_match(match_id: int, update: MatchReviewUpdate):
    allowed_statuses = {"Pending", "Confirmed", "Rejected", "Uncertain"}
    if update.review_status not in allowed_statuses:
        raise HTTPException(status_code=400, detail="Unsupported review status")

    with engine.begin() as connection:
        result = connection.execute(text("""
            UPDATE need_artifact_matches
            SET relationship_type = :relationship_type,
                review_status = :review_status,
                reviewer = :reviewer,
                review_notes = :review_notes,
                reviewed_at = NOW(),
                updated_at = NOW()
            WHERE match_id = :match_id
        """), {
            "match_id": match_id,
            "relationship_type": update.relationship_type,
            "review_status": update.review_status,
            "reviewer": update.reviewer,
            "review_notes": update.review_notes,
        })
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Match not found")
    return {"updated_match_id": match_id}


@app.get("/needs/{need_code}/artifacts")
def need_artifacts(need_code: str):
    with engine.connect() as connection:
        records = connection.execute(text("""
            SELECT nam.match_id, nam.relationship_type, nam.overall_score,
                   nam.review_status, nam.match_explanation,
                   ia.artifact_code, ia.artifact_type, ia.external_number,
                   ia.title, ia.state, ia.external_url,
                   t.tool_code, t.tool_name,
                   es.owner_name, es.repository_name
            FROM need_artifact_matches nam
            JOIN needs n ON n.need_id = nam.need_id
            JOIN implementation_artifacts ia ON ia.artifact_id = nam.artifact_id
            JOIN tools t ON t.tool_id = ia.tool_id
            JOIN external_sources es ON es.external_source_id = ia.external_source_id
            WHERE n.need_code = :need_code
            ORDER BY CASE nam.review_status WHEN 'Confirmed' THEN 0 WHEN 'Pending' THEN 1 ELSE 2 END,
                     nam.overall_score DESC
        """), {"need_code": need_code}).mappings().all()
    return [dict(record) for record in records]
