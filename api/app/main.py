import json
import os
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import create_engine, text


DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=5,
    max_overflow=5,
)

app = FastAPI(
    title="UWG Community Needs API",
    version="0.1.0",
)


class NeedUpdate(BaseModel):
    canonical_need: Optional[str] = None
    desired_outcome: Optional[str] = None
    lifecycle_status: Optional[str] = None
    priority: Optional[str] = None
    human_reviewed: Optional[bool] = None
    reviewer: Optional[str] = None
    notes: Optional[str] = None


@app.get("/health")
def health():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return {"status": "ok"}


@app.get("/dashboard/summary")
def dashboard_summary():
    with engine.connect() as connection:
        totals = connection.execute(
            text(
                """
                SELECT
                    (SELECT COUNT(*) FROM needs) AS needs,
                    (SELECT COUNT(*) FROM evidence) AS evidence,
                    (SELECT COUNT(*) FROM sources) AS sources,
                    (SELECT COUNT(*) FROM organizations) AS organizations
                """
            )
        ).mappings().one()

        topics = connection.execute(
            text(
                """
                SELECT
                    COALESCE(need_category, 'Uncategorized') AS need_category,
                    COUNT(*) AS need_count
                FROM needs
                GROUP BY COALESCE(need_category, 'Uncategorized')
                ORDER BY need_count DESC
                """
            )
        ).mappings().all()

    return {
        "totals": dict(totals),
        "topics": [dict(row) for row in topics],
    }


@app.get("/needs")
def list_needs(
    q: str = "",
    category: str = "",
    reviewed: Optional[bool] = None,
    limit: int = Query(100, ge=1, le=500),
):
    conditions = ["1=1"]
    parameters = {"limit": limit}

    if q:
        conditions.append(
            "(canonical_need LIKE :search "
            "OR need_summary LIKE :search "
            "OR need_code LIKE :search)"
        )
        parameters["search"] = f"%{q}%"

    if category:
        conditions.append("need_category = :category")
        parameters["category"] = category

    if reviewed is not None:
        conditions.append("human_reviewed = :reviewed")
        parameters["reviewed"] = reviewed

    query = f"""
        SELECT *
        FROM v_need_summary
        WHERE {" AND ".join(conditions)}
        ORDER BY signal_score DESC, evidence_count DESC, need_code
        LIMIT :limit
    """

    with engine.connect() as connection:
        records = connection.execute(
            text(query),
            parameters,
        ).mappings().all()

    return [dict(record) for record in records]


@app.get("/needs/{need_code}")
def get_need(need_code: str):
    with engine.connect() as connection:
        need = connection.execute(
            text(
                """
                SELECT *
                FROM v_need_summary
                WHERE need_code = :need_code
                """
            ),
            {"need_code": need_code},
        ).mappings().first()

        if not need:
            raise HTTPException(
                status_code=404,
                detail="Need not found",
            )

        evidence = connection.execute(
            text(
                """
                SELECT
                    e.evidence_code,
                    e.original_statement,
                    e.normalized_statement,
                    e.evidence_type,
                    e.event_year,
                    e.user_community,
                    e.source_location,
                    e.human_reviewed,
                    o.organization_name,
                    s.source_title
                FROM evidence e
                JOIN needs n
                  ON n.need_id = e.need_id
                LEFT JOIN organizations o
                  ON o.organization_id = e.organization_id
                LEFT JOIN sources s
                  ON s.source_id = e.source_id
                WHERE n.need_code = :need_code
                ORDER BY e.event_year DESC, e.evidence_code
                """
            ),
            {"need_code": need_code},
        ).mappings().all()

    return {
        "need": dict(need),
        "evidence": [dict(record) for record in evidence],
    }


@app.patch("/needs/{need_code}")
def update_need(
    need_code: str,
    update: NeedUpdate,
):
    values = update.model_dump(exclude_none=True)

    if not values:
        raise HTTPException(
            status_code=400,
            detail="No update fields supplied",
        )

    allowed_fields = {
        "canonical_need",
        "desired_outcome",
        "lifecycle_status",
        "priority",
        "human_reviewed",
        "reviewer",
        "notes",
    }

    values = {
        key: value
        for key, value in values.items()
        if key in allowed_fields
    }

    assignments = ", ".join(
        f"{field} = :{field}"
        for field in values
    )

    values["need_code"] = need_code

    with engine.begin() as connection:
        result = connection.execute(
            text(
                f"""
                UPDATE needs
                SET
                    {assignments},
                    review_date = NOW()
                WHERE need_code = :need_code
                """
            ),
            values,
        )

        if result.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Need not found",
            )

        audit_values = {
            key: value
            for key, value in values.items()
            if key != "need_code"
        }

        connection.execute(
            text(
                """
                INSERT INTO review_decisions (
                    entity_type,
                    entity_key,
                    decision_type,
                    new_value,
                    reviewer
                )
                VALUES (
                    'Need',
                    :need_code,
                    'Edit',
                    :new_value,
                    :reviewer
                )
                """
            ),
            {
                "need_code": need_code,
                "new_value": json.dumps(
                    audit_values,
                    default=str,
                ),
                "reviewer": values.get(
                    "reviewer",
                    "local-demo",
                ),
            },
        )

    return {"updated": need_code}

@app.get("/evidence")
def list_evidence(
    q: str = "",
    reviewed: Optional[bool] = None,
    limit: int = Query(200, ge=1, le=1000),
):
    conditions = ["1=1"]
    parameters = {"limit": limit}

    if q:
        conditions.append(
            "("
            "e.original_statement LIKE :search "
            "OR e.normalized_statement LIKE :search "
            "OR e.evidence_code LIKE :search "
            "OR o.organization_name LIKE :search"
            ")"
        )
        parameters["search"] = f"%{q}%"

    if reviewed is not None:
        conditions.append(
            "e.human_reviewed = :reviewed"
        )
        parameters["reviewed"] = reviewed

    query = f"""
        SELECT
            e.evidence_code,
            n.need_code,
            e.original_statement,
            e.normalized_statement,
            e.evidence_type,
            e.event_year,
            e.user_community,
            e.evidence_strength,
            e.match_confidence,
            e.source_location,
            e.human_reviewed,
            o.organization_name,
            s.source_code,
            s.source_title
        FROM evidence e
        LEFT JOIN needs n
          ON n.need_id = e.need_id
        LEFT JOIN organizations o
          ON o.organization_id = e.organization_id
        LEFT JOIN sources s
          ON s.source_id = e.source_id
        WHERE {" AND ".join(conditions)}
        ORDER BY
            e.human_reviewed,
            e.event_year DESC,
            e.evidence_code
        LIMIT :limit
    """

    with engine.connect() as connection:
        records = connection.execute(
            text(query),
            parameters,
        ).mappings().all()

    return [dict(record) for record in records]


@app.get("/evidence/{evidence_code}")
def get_evidence(evidence_code: str):
    with engine.connect() as connection:
        record = connection.execute(
            text(
                """
                SELECT
                    e.*,
                    n.need_code,
                    n.canonical_need,
                    o.organization_name,
                    s.source_code,
                    s.source_title,
                    s.source_year,
                    s.file_name
                FROM evidence e
                LEFT JOIN needs n
                  ON n.need_id = e.need_id
                LEFT JOIN organizations o
                  ON o.organization_id = e.organization_id
                LEFT JOIN sources s
                  ON s.source_id = e.source_id
                WHERE e.evidence_code = :code
                """
            ),
            {"code": evidence_code},
        ).mappings().first()

    if not record:
        raise HTTPException(
            status_code=404,
            detail="Evidence not found",
        )

    return dict(record)


@app.get("/organizations")
def list_organizations():
    with engine.connect() as connection:
        records = connection.execute(
            text(
                """
                SELECT
                    o.organization_id,
                    o.organization_name,
                    o.organization_type,
                    COUNT(DISTINCT e.evidence_id)
                        AS evidence_count,
                    COUNT(DISTINCT e.need_id)
                        AS need_count,
                    MIN(e.event_year)
                        AS first_seen_year,
                    MAX(e.event_year)
                        AS last_seen_year
                FROM organizations o
                LEFT JOIN evidence e
                  ON e.organization_id =
                     o.organization_id
                GROUP BY
                    o.organization_id,
                    o.organization_name,
                    o.organization_type
                ORDER BY evidence_count DESC
                """
            )
        ).mappings().all()

    return [dict(record) for record in records]


@app.get("/sources")
def list_sources():
    with engine.connect() as connection:
        records = connection.execute(
            text(
                """
                SELECT
                    s.source_code,
                    s.source_title,
                    s.source_type,
                    s.source_year,
                    s.file_name,
                    COUNT(DISTINCT e.evidence_id)
                        AS evidence_count,
                    COUNT(DISTINCT e.need_id)
                        AS need_count
                FROM sources s
                LEFT JOIN evidence e
                  ON e.source_id = s.source_id
                GROUP BY
                    s.source_id,
                    s.source_code,
                    s.source_title,
                    s.source_type,
                    s.source_year,
                    s.file_name
                ORDER BY s.source_year DESC
                """
            )
        ).mappings().all()

    return [dict(record) for record in records]