-- Earthdata Community Insights v2
-- Additive migration for evidence-based investment prioritization.
--
-- This migration intentionally preserves the current prototype tables and APIs.
-- It introduces new relationship, assessment, organizational-mapping, and
-- initiative tables without removing evidence.need_id or changing existing views.

START TRANSACTION;

-- ---------------------------------------------------------------------------
-- Evidence provenance additions
-- ---------------------------------------------------------------------------

ALTER TABLE evidence
    ADD COLUMN IF NOT EXISTS source_section VARCHAR(500) NULL AFTER source_location,
    ADD COLUMN IF NOT EXISTS source_page VARCHAR(100) NULL AFTER source_section,
    ADD COLUMN IF NOT EXISTS originating_organization_name VARCHAR(255) NULL
        AFTER organization_id,
    ADD COLUMN IF NOT EXISTS immutable_at DATETIME NULL AFTER context_rationale;

-- Preserve the organization name as it was known when the evidence was captured.
UPDATE evidence e
LEFT JOIN organizations o
    ON o.organization_id = e.organization_id
SET e.originating_organization_name = o.organization_name
WHERE e.originating_organization_name IS NULL;

-- Existing rows become immutable once this migration is applied. New importers
-- should set immutable_at when the evidence record is accepted into the corpus.
UPDATE evidence
SET immutable_at = CURRENT_TIMESTAMP
WHERE immutable_at IS NULL;

-- ---------------------------------------------------------------------------
-- Many-to-many evidence-to-need relationships
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS evidence_need_links (
    evidence_need_link_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    evidence_id BIGINT UNSIGNED NOT NULL,
    need_id BIGINT UNSIGNED NOT NULL,
    relationship_type VARCHAR(50) NOT NULL DEFAULT 'Supports',
    confidence DECIMAL(5,4),
    mapping_method VARCHAR(100),
    review_status VARCHAR(50) NOT NULL DEFAULT 'Candidate',
    reviewer VARCHAR(255),
    reviewed_at DATETIME,
    notes TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_evidence_need_link_evidence
        FOREIGN KEY (evidence_id)
        REFERENCES evidence(evidence_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_evidence_need_link_need
        FOREIGN KEY (need_id)
        REFERENCES needs(need_id)
        ON DELETE CASCADE,

    CONSTRAINT uq_evidence_need_link
        UNIQUE (evidence_id, need_id, relationship_type),

    INDEX idx_enl_need (need_id),
    INDEX idx_enl_review_status (review_status)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;

-- Backfill the current one-to-many relationship. The legacy evidence.need_id
-- remains in place during the compatibility period.
INSERT IGNORE INTO evidence_need_links (
    evidence_id,
    need_id,
    relationship_type,
    confidence,
    mapping_method,
    review_status,
    reviewer,
    reviewed_at,
    notes
)
SELECT
    e.evidence_id,
    e.need_id,
    'Supports',
    e.match_confidence,
    COALESCE(e.match_method, 'Legacy evidence.need_id'),
    CASE
        WHEN e.human_reviewed = TRUE THEN 'Confirmed'
        ELSE 'Candidate'
    END,
    NULL,
    NULL,
    'Backfilled from evidence.need_id by migration 010.'
FROM evidence e
WHERE e.need_id IS NOT NULL;

-- ---------------------------------------------------------------------------
-- Science Spheres and historical organization mappings
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS science_spheres (
    sphere_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    sphere_code VARCHAR(50) NOT NULL UNIQUE,
    sphere_name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS organization_sphere_mappings (
    organization_sphere_mapping_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    organization_id BIGINT UNSIGNED NOT NULL,
    sphere_id BIGINT UNSIGNED NOT NULL,
    relationship_type VARCHAR(50) NOT NULL DEFAULT 'Successor',
    effective_start DATE,
    effective_end DATE,
    confidence VARCHAR(20) NOT NULL DEFAULT 'Unreviewed',
    reviewed BOOLEAN NOT NULL DEFAULT FALSE,
    reviewer VARCHAR(255),
    review_notes TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_org_sphere_org
        FOREIGN KEY (organization_id)
        REFERENCES organizations(organization_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_org_sphere_sphere
        FOREIGN KEY (sphere_id)
        REFERENCES science_spheres(sphere_id)
        ON DELETE CASCADE,

    CONSTRAINT uq_org_sphere_period
        UNIQUE (organization_id, sphere_id, effective_start),

    INDEX idx_org_sphere_sphere (sphere_id),
    INDEX idx_org_sphere_dates (effective_start, effective_end)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- Reviewer-controlled need impact and gap assessments
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS need_assessments (
    need_assessment_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    need_id BIGINT UNSIGNED NOT NULL,
    assessment_version INT UNSIGNED NOT NULL DEFAULT 1,
    assessment_status VARCHAR(30) NOT NULL DEFAULT 'Draft',

    -- Explainable impact components. Each component is 0-100.
    evidence_strength_score DECIMAL(5,2),
    source_breadth_score DECIMAL(5,2),
    persistence_score DECIMAL(5,2),
    community_breadth_score DECIMAL(5,2),
    strategic_alignment_score DECIMAL(5,2),

    -- Human-reviewed coverage/gap assessment.
    coverage_status VARCHAR(30) NOT NULL DEFAULT 'Unassessed',
    gap_severity_score DECIMAL(5,2),
    gap_rationale TEXT,

    -- Derived or reviewer-adjusted outputs.
    calculated_impact_score DECIMAL(5,2),
    reviewer_impact_score DECIMAL(5,2),
    calculated_opportunity_score DECIMAL(5,2),
    reviewer_opportunity_score DECIMAL(5,2),

    scoring_method_version VARCHAR(30),
    assessed_by VARCHAR(255),
    assessed_at DATETIME,
    approved_by VARCHAR(255),
    approved_at DATETIME,
    review_notes TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_need_assessment_need
        FOREIGN KEY (need_id)
        REFERENCES needs(need_id)
        ON DELETE CASCADE,

    CONSTRAINT uq_need_assessment_version
        UNIQUE (need_id, assessment_version),

    INDEX idx_need_assessment_status (assessment_status),
    INDEX idx_need_assessment_coverage (coverage_status),
    INDEX idx_need_assessment_opportunity (calculated_opportunity_score)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- Development initiatives and the needs/capabilities they address
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS initiatives (
    initiative_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    initiative_code VARCHAR(50) NOT NULL UNIQUE,
    initiative_name VARCHAR(255) NOT NULL,
    description TEXT,
    initiative_status VARCHAR(50) NOT NULL DEFAULT 'Proposed',
    owning_organization_id BIGINT UNSIGNED,
    start_date DATE,
    target_date DATE,
    source_url VARCHAR(1000),
    notes TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_initiative_owner
        FOREIGN KEY (owning_organization_id)
        REFERENCES organizations(organization_id)
        ON DELETE SET NULL,

    INDEX idx_initiative_status (initiative_status)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS initiative_needs (
    initiative_need_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    initiative_id BIGINT UNSIGNED NOT NULL,
    need_id BIGINT UNSIGNED NOT NULL,
    relationship_type VARCHAR(50) NOT NULL DEFAULT 'Addresses',
    expected_coverage VARCHAR(30) NOT NULL DEFAULT 'Unknown',
    expected_impact_score DECIMAL(5,2),
    review_status VARCHAR(30) NOT NULL DEFAULT 'Candidate',
    reviewer VARCHAR(255),
    reviewed_at DATETIME,
    notes TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_initiative_need_initiative
        FOREIGN KEY (initiative_id)
        REFERENCES initiatives(initiative_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_initiative_need_need
        FOREIGN KEY (need_id)
        REFERENCES needs(need_id)
        ON DELETE CASCADE,

    CONSTRAINT uq_initiative_need
        UNIQUE (initiative_id, need_id, relationship_type),

    INDEX idx_initiative_need_need (need_id),
    INDEX idx_initiative_need_review (review_status)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS initiative_capabilities (
    initiative_capability_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    initiative_id BIGINT UNSIGNED NOT NULL,
    capability_id BIGINT UNSIGNED NOT NULL,
    relationship_type VARCHAR(50) NOT NULL DEFAULT 'Delivers',
    review_status VARCHAR(30) NOT NULL DEFAULT 'Candidate',
    reviewer VARCHAR(255),
    reviewed_at DATETIME,
    notes TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_initiative_capability_initiative
        FOREIGN KEY (initiative_id)
        REFERENCES initiatives(initiative_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_initiative_capability_capability
        FOREIGN KEY (capability_id)
        REFERENCES capabilities(capability_id)
        ON DELETE CASCADE,

    CONSTRAINT uq_initiative_capability
        UNIQUE (initiative_id, capability_id, relationship_type),

    INDEX idx_initiative_capability_capability (capability_id),
    INDEX idx_initiative_capability_review (review_status)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- Explainable summary views
-- ---------------------------------------------------------------------------

CREATE OR REPLACE VIEW v_need_evidence_summary_v2 AS
SELECT
    n.need_id,
    n.need_code,
    n.canonical_need,
    n.need_category,
    n.lifecycle_status,
    COUNT(DISTINCT enl.evidence_id) AS evidence_count,
    COUNT(DISTINCT e.source_id) AS source_count,
    COUNT(DISTINCT e.organization_id) AS originating_organization_count,
    COUNT(DISTINCT e.event_year) AS year_count,
    MIN(e.event_year) AS first_seen_year,
    MAX(e.event_year) AS last_seen_year
FROM needs n
LEFT JOIN evidence_need_links enl
    ON enl.need_id = n.need_id
   AND enl.review_status IN ('Candidate', 'Confirmed')
LEFT JOIN evidence e
    ON e.evidence_id = enl.evidence_id
   AND e.duplicate_evidence = FALSE
GROUP BY
    n.need_id,
    n.need_code,
    n.canonical_need,
    n.need_category,
    n.lifecycle_status;

CREATE OR REPLACE VIEW v_current_need_assessments AS
SELECT na.*
FROM need_assessments na
JOIN (
    SELECT need_id, MAX(assessment_version) AS assessment_version
    FROM need_assessments
    GROUP BY need_id
) latest
  ON latest.need_id = na.need_id
 AND latest.assessment_version = na.assessment_version;

CREATE OR REPLACE VIEW v_investment_opportunities AS
SELECT
    n.need_id,
    n.need_code,
    n.canonical_need,
    n.need_category,
    es.evidence_count,
    es.source_count,
    es.originating_organization_count,
    es.year_count,
    es.first_seen_year,
    es.last_seen_year,
    a.assessment_status,
    a.coverage_status,
    COALESCE(a.reviewer_impact_score, a.calculated_impact_score) AS impact_score,
    a.gap_severity_score,
    COALESCE(
        a.reviewer_opportunity_score,
        a.calculated_opportunity_score
    ) AS opportunity_score,
    a.gap_rationale,
    a.scoring_method_version,
    a.approved_by,
    a.approved_at
FROM needs n
LEFT JOIN v_need_evidence_summary_v2 es
    ON es.need_id = n.need_id
LEFT JOIN v_current_need_assessments a
    ON a.need_id = n.need_id;

COMMIT;
