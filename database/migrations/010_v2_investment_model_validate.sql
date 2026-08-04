-- Validation queries for migration 010_v2_investment_model.sql
-- Each result should be reviewed after applying the migration to a test database.

-- 1. Expected: 0
SELECT COUNT(*) AS missing_backfilled_evidence_need_links
FROM evidence e
LEFT JOIN evidence_need_links enl
  ON enl.evidence_id = e.evidence_id
 AND enl.need_id = e.need_id
 AND enl.relationship_type = 'Supports'
WHERE e.need_id IS NOT NULL
  AND enl.evidence_need_link_id IS NULL;

-- 2. Expected: evidence_count equals the number of rows in evidence.
SELECT
    (SELECT COUNT(*) FROM evidence) AS evidence_count,
    (SELECT COUNT(*) FROM evidence WHERE immutable_at IS NOT NULL)
        AS evidence_with_immutable_timestamp;

-- 3. Expected: 0 for records with a linked organization.
SELECT COUNT(*) AS missing_captured_organization_names
FROM evidence e
WHERE e.organization_id IS NOT NULL
  AND (
      e.originating_organization_name IS NULL
      OR TRIM(e.originating_organization_name) = ''
  );

-- 4. Expected: one row per need, with existing evidence totals represented.
SELECT *
FROM v_need_evidence_summary_v2
ORDER BY evidence_count DESC, need_code
LIMIT 25;

-- 5. Expected initially: 0, unless test assessments were added.
SELECT COUNT(*) AS need_assessment_count
FROM need_assessments;

-- 6. Expected: 0. Approved assessments must include approval metadata.
SELECT COUNT(*) AS invalid_approved_assessments
FROM need_assessments
WHERE assessment_status = 'Approved'
  AND (approved_by IS NULL OR approved_at IS NULL);

-- 7. Expected: 0. A Sphere mapping should not exist without review metadata
-- once it is marked reviewed.
SELECT COUNT(*) AS invalid_reviewed_sphere_mappings
FROM organization_sphere_mappings
WHERE reviewed = TRUE
  AND (reviewer IS NULL OR TRIM(reviewer) = '');

-- 8. Inspect current opportunities. Empty assessment fields are expected until
-- reviewer-controlled assessments are created.
SELECT
    need_code,
    canonical_need,
    evidence_count,
    source_count,
    originating_organization_count,
    year_count,
    assessment_status,
    coverage_status,
    impact_score,
    gap_severity_score,
    opportunity_score
FROM v_investment_opportunities
ORDER BY
    opportunity_score DESC,
    evidence_count DESC,
    need_code
LIMIT 50;
