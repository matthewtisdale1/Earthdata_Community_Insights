-- Migration 004: documentation-first solution evidence

CREATE TABLE IF NOT EXISTS solution_evidence (
    solution_evidence_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    evidence_code VARCHAR(160) NOT NULL UNIQUE,
    tool_id BIGINT UNSIGNED NOT NULL,
    capability_id BIGINT UNSIGNED,
    evidence_type VARCHAR(50) NOT NULL,
    evidence_role VARCHAR(80) NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    supporting_excerpt TEXT,
    source_url TEXT NOT NULL,
    source_name VARCHAR(255),
    version_label VARCHAR(100),
    published_at DATETIME,
    last_verified_at DATETIME,
    review_status VARCHAR(40) NOT NULL DEFAULT 'Pending',
    reviewer VARCHAR(255),
    review_notes TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_solution_evidence_tool
        FOREIGN KEY (tool_id) REFERENCES tools(tool_id) ON DELETE CASCADE,
    CONSTRAINT fk_solution_evidence_capability
        FOREIGN KEY (capability_id) REFERENCES capabilities(capability_id) ON DELETE CASCADE,

    INDEX idx_solution_evidence_tool (tool_id),
    INDEX idx_solution_evidence_capability (capability_id),
    INDEX idx_solution_evidence_type_role (evidence_type, evidence_role),
    INDEX idx_solution_evidence_review (review_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Curated, official Harmony evidence for the NEED-0042 demonstration.
INSERT INTO solution_evidence (
    evidence_code, tool_id, capability_id, evidence_type, evidence_role,
    title, description, supporting_excerpt, source_url, source_name,
    review_status, reviewer, review_notes, last_verified_at
)
SELECT
    CONCAT('HARMONY-DOC-', c.capability_code),
    t.tool_id,
    c.capability_id,
    'documentation',
    'Capability Evidence',
    'Harmony Documentation',
    'Official Harmony service and API documentation describing supported transformation and subsetting capabilities.',
    CASE c.capability_code
        WHEN 'SPATIAL_SUBSETTING' THEN 'Harmony documents bounding-box and shape subsetting capabilities and exposes collection capability flags for bboxSubset and shapeSubset.'
        WHEN 'VARIABLE_SUBSETTING' THEN 'Harmony documents variable subsetting and exposes a collection capability flag named variableSubset.'
        WHEN 'TEMPORAL_SUBSETTING' THEN 'Harmony documents temporal subsetting parameters and services that support temporal subsetting.'
    END,
    'https://harmony.earthdata.nasa.gov/docs',
    'NASA Earthdata Harmony',
    'Confirmed',
    'prototype-seed',
    'Official product documentation used as the primary proof that Harmony currently provides this capability.',
    NOW()
FROM tools t
JOIN capabilities c ON c.capability_code IN (
    'SPATIAL_SUBSETTING', 'VARIABLE_SUBSETTING', 'TEMPORAL_SUBSETTING'
)
WHERE t.tool_code = 'HARMONY'
ON DUPLICATE KEY UPDATE
    title = VALUES(title),
    description = VALUES(description),
    supporting_excerpt = VALUES(supporting_excerpt),
    source_url = VALUES(source_url),
    review_status = VALUES(review_status),
    review_notes = VALUES(review_notes),
    last_verified_at = VALUES(last_verified_at);

INSERT INTO solution_evidence (
    evidence_code, tool_id, capability_id, evidence_type, evidence_role,
    title, description, supporting_excerpt, source_url, source_name,
    review_status, reviewer, review_notes, last_verified_at
)
SELECT
    'HARMONY-TUTORIAL-SUBSETTING',
    t.tool_id,
    c.capability_id,
    'tutorial',
    'Usage Guidance',
    'Harmony API Introduction Notebook',
    'Official example notebook demonstrating Harmony subsetting and reprojection requests.',
    'The notebook provides examples of synchronous and asynchronous access to Harmony subsetting and reprojection services.',
    'https://harmony.earthdata.nasa.gov/notebook-example.html',
    'NASA Earthdata Harmony',
    'Confirmed',
    'prototype-seed',
    'Official usage example supporting the spatial-subsetting demonstration.',
    NOW()
FROM tools t
JOIN capabilities c ON c.capability_code = 'SPATIAL_SUBSETTING'
WHERE t.tool_code = 'HARMONY'
ON DUPLICATE KEY UPDATE
    title = VALUES(title),
    description = VALUES(description),
    supporting_excerpt = VALUES(supporting_excerpt),
    source_url = VALUES(source_url),
    review_status = VALUES(review_status),
    review_notes = VALUES(review_notes),
    last_verified_at = VALUES(last_verified_at);

CREATE OR REPLACE VIEW v_capability_solution_evidence AS
SELECT
    se.solution_evidence_id,
    se.evidence_code,
    c.capability_code,
    c.capability_name,
    t.tool_code,
    t.tool_name,
    se.evidence_type,
    se.evidence_role,
    se.title,
    se.description,
    se.supporting_excerpt,
    se.source_url,
    se.source_name,
    se.version_label,
    se.published_at,
    se.last_verified_at,
    se.review_status,
    se.reviewer,
    se.review_notes
FROM solution_evidence se
JOIN tools t ON t.tool_id = se.tool_id
LEFT JOIN capabilities c ON c.capability_id = se.capability_id;
