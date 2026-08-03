import math
import os

import pandas as pd
from sqlalchemy import create_engine, text


DATABASE_URL = os.environ["DATABASE_URL"]
WORKBOOK_PATH = os.environ["WORKBOOK_PATH"]

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)


def clean(value):
    if pd.isna(value):
        return None

    if isinstance(value, float) and math.isnan(value):
        return None

    return value


def as_bool(value):
    return str(value).strip().lower() in {
        "yes",
        "true",
        "1",
        "y",
    }


def get_or_create_organization(connection, name):
    name = clean(name)

    if not name:
        return None

    connection.execute(
        text(
            """
            INSERT INTO organizations (
                organization_name,
                organization_type
            )
            VALUES (
                :name,
                'UWG / Organization'
            )
            ON DUPLICATE KEY UPDATE
                organization_name = VALUES(organization_name)
            """
        ),
        {"name": name},
    )

    return connection.execute(
        text(
            """
            SELECT organization_id
            FROM organizations
            WHERE organization_name = :name
            """
        ),
        {"name": name},
    ).scalar_one()


def run_import():
    workbook = pd.ExcelFile(WORKBOOK_PATH)

    print("Workbook sheets:", workbook.sheet_names)

    with engine.begin() as connection:
        sources = pd.read_excel(
            workbook,
            "Sources",
        )

        for _, row in sources.iterrows():
            connection.execute(
                text(
                    """
                    INSERT INTO sources (
                        source_code,
                        source_title,
                        source_type,
                        source_year,
                        file_name,
                        notes
                    )
                    VALUES (
                        :source_code,
                        :source_title,
                        :source_type,
                        :source_year,
                        :file_name,
                        :notes
                    )
                    ON DUPLICATE KEY UPDATE
                        source_title = VALUES(source_title),
                        source_type = VALUES(source_type),
                        source_year = VALUES(source_year),
                        file_name = VALUES(file_name),
                        notes = VALUES(notes)
                    """
                ),
                {
                    "source_code": clean(row.get("Source ID")),
                    "source_title": clean(
                        row.get("Source Title")
                    ),
                    "source_type": clean(
                        row.get("Source Type")
                    ),
                    "source_year": clean(
                        row.get("Source Year")
                    ),
                    "file_name": clean(
                        row.get("File Name")
                    ),
                    "notes": clean(row.get("Notes")),
                },
            )

        needs = pd.read_excel(
            workbook,
            "Needs",
        )

        for _, row in needs.iterrows():
            connection.execute(
                text(
                    """
                    INSERT INTO needs (
                        need_code,
                        canonical_need,
                        need_summary,
                        need_category,
                        desired_outcome,
                        lifecycle_status,
                        priority,
                        trend,
                        human_reviewed,
                        reviewer,
                        notes
                    )
                    VALUES (
                        :need_code,
                        :canonical_need,
                        :need_summary,
                        :need_category,
                        :desired_outcome,
                        :lifecycle_status,
                        :priority,
                        :trend,
                        :human_reviewed,
                        :reviewer,
                        :notes
                    )
                    ON DUPLICATE KEY UPDATE
                        canonical_need =
                            VALUES(canonical_need),
                        need_summary =
                            VALUES(need_summary),
                        need_category =
                            VALUES(need_category),
                        desired_outcome =
                            VALUES(desired_outcome),
                        lifecycle_status =
                            VALUES(lifecycle_status),
                        priority =
                            VALUES(priority),
                        trend =
                            VALUES(trend),
                        human_reviewed =
                            VALUES(human_reviewed),
                        reviewer =
                            VALUES(reviewer),
                        notes =
                            VALUES(notes)
                    """
                ),
                {
                    "need_code": clean(
                        row.get("Need ID")
                    ),
                    "canonical_need": clean(
                        row.get("Canonical Need (Draft)")
                    ) or "",
                    "need_summary": clean(
                        row.get("Need Summary")
                    ),
                    "need_category": clean(
                        row.get("Need Category")
                    ),
                    "desired_outcome": clean(
                        row.get("Desired Outcome")
                    ),
                    "lifecycle_status": clean(
                        row.get("Lifecycle Status")
                    ) or "Candidate",
                    "priority": clean(
                        row.get("Priority")
                    ) or "Unassigned",
                    "trend": clean(
                        row.get("Trend")
                    ),
                    "human_reviewed": as_bool(
                        row.get("Human Reviewed")
                    ),
                    "reviewer": clean(
                        row.get("Reviewer")
                    ),
                    "notes": clean(
                        row.get("Notes")
                    ),
                },
            )

        evidence = pd.read_excel(
            workbook,
            "Evidence",
        )

        for _, row in evidence.iterrows():
            need_id = connection.execute(
                text(
                    """
                    SELECT need_id
                    FROM needs
                    WHERE need_code = :need_code
                    """
                ),
                {
                    "need_code": clean(
                        row.get("Need ID")
                    )
                },
            ).scalar()

            source_id = connection.execute(
                text(
                    """
                    SELECT source_id
                    FROM sources
                    WHERE source_code = :source_code
                    """
                ),
                {
                    "source_code": clean(
                        row.get("Source ID")
                    )
                },
            ).scalar_one()

            organization_id = (
                get_or_create_organization(
                    connection,
                    row.get("Organization"),
                )
            )

            connection.execute(
                text(
                    """
                    INSERT INTO evidence (
                        evidence_code,
                        need_id,
                        source_id,
                        organization_id,
                        original_statement,
                        normalized_statement,
                        evidence_type,
                        event_year,
                        user_community,
                        evidence_strength,
                        match_confidence,
                        match_method,
                        source_location,
                        human_reviewed,
                        duplicate_evidence,
                        context_rationale
                    )
                    VALUES (
                        :evidence_code,
                        :need_id,
                        :source_id,
                        :organization_id,
                        :original_statement,
                        :normalized_statement,
                        :evidence_type,
                        :event_year,
                        :user_community,
                        :evidence_strength,
                        :match_confidence,
                        :match_method,
                        :source_location,
                        :human_reviewed,
                        :duplicate_evidence,
                        :context_rationale
                    )
                    ON DUPLICATE KEY UPDATE
                        need_id =
                            VALUES(need_id),
                        source_id =
                            VALUES(source_id),
                        organization_id =
                            VALUES(organization_id),
                        original_statement =
                            VALUES(original_statement),
                        normalized_statement =
                            VALUES(normalized_statement),
                        event_year =
                            VALUES(event_year),
                        user_community =
                            VALUES(user_community),
                        human_reviewed =
                            VALUES(human_reviewed),
                        context_rationale =
                            VALUES(context_rationale)
                    """
                ),
                {
                    "evidence_code": clean(
                        row.get("Evidence ID")
                    ),
                    "need_id": need_id,
                    "source_id": source_id,
                    "organization_id":
                        organization_id,
                    "original_statement": clean(
                        row.get("Original Statement")
                    ) or "",
                    "normalized_statement": clean(
                        row.get("Normalized Statement")
                    ),
                    "evidence_type": clean(
                        row.get("Evidence Type")
                    ),
                    "event_year": clean(
                        row.get("Event Year")
                    ),
                    "user_community": clean(
                        row.get("User Community")
                    ),
                    "evidence_strength": clean(
                        row.get("Evidence Strength")
                    ),
                    "match_confidence": clean(
                        row.get("Match Confidence")
                    ),
                    "match_method": clean(
                        row.get("Match Method")
                    ),
                    "source_location": clean(
                        row.get("Source Location")
                    ),
                    "human_reviewed": as_bool(
                        row.get("Human Reviewed")
                    ),
                    "duplicate_evidence": as_bool(
                        row.get("Duplicate Evidence")
                    ),
                    "context_rationale": clean(
                        row.get("Context / Rationale")
                    ),
                },
            )

        totals = connection.execute(
            text(
                """
                SELECT
                    (SELECT COUNT(*) FROM needs)
                        AS needs,
                    (SELECT COUNT(*) FROM evidence)
                        AS evidence,
                    (SELECT COUNT(*) FROM sources)
                        AS sources,
                    (SELECT COUNT(*) FROM organizations)
                        AS organizations
                """
            )
        ).mappings().one()

        print("Import complete:", dict(totals))


if __name__ == "__main__":
    run_import()