CREATE TABLE organizations (
    organization_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    organization_name VARCHAR(255) NOT NULL UNIQUE,
    organization_type VARCHAR(100)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


CREATE TABLE sources (
    source_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    source_code VARCHAR(40) NOT NULL UNIQUE,
    source_title VARCHAR(500) NOT NULL,
    source_type VARCHAR(100),
    source_year SMALLINT UNSIGNED,
    file_name VARCHAR(500),
    notes TEXT
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


CREATE TABLE needs (
    need_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    need_code VARCHAR(40) NOT NULL UNIQUE,
    canonical_need TEXT NOT NULL,
    need_summary VARCHAR(500),
    need_category VARCHAR(150),
    desired_outcome TEXT,
    lifecycle_status VARCHAR(50) DEFAULT 'Candidate',
    priority VARCHAR(30) DEFAULT 'Unassigned',
    trend VARCHAR(50),
    human_reviewed BOOLEAN DEFAULT FALSE,
    reviewer VARCHAR(255),
    review_date DATETIME,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_need_category (need_category),
    INDEX idx_need_status (lifecycle_status)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


CREATE TABLE evidence (
    evidence_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    evidence_code VARCHAR(40) NOT NULL UNIQUE,
    need_id BIGINT UNSIGNED,
    source_id BIGINT UNSIGNED NOT NULL,
    organization_id BIGINT UNSIGNED,
    original_statement LONGTEXT NOT NULL,
    normalized_statement TEXT,
    evidence_type VARCHAR(100),
    event_year SMALLINT UNSIGNED,
    user_community VARCHAR(500),
    evidence_strength VARCHAR(30),
    match_confidence DECIMAL(5,4),
    match_method VARCHAR(255),
    source_location VARCHAR(500),
    human_reviewed BOOLEAN DEFAULT FALSE,
    duplicate_evidence BOOLEAN DEFAULT FALSE,
    context_rationale LONGTEXT,

    CONSTRAINT fk_evidence_need
        FOREIGN KEY (need_id)
        REFERENCES needs(need_id),

    CONSTRAINT fk_evidence_source
        FOREIGN KEY (source_id)
        REFERENCES sources(source_id),

    CONSTRAINT fk_evidence_org
        FOREIGN KEY (organization_id)
        REFERENCES organizations(organization_id),

    INDEX idx_evidence_need (need_id),
    INDEX idx_evidence_year (event_year),

    FULLTEXT INDEX ft_evidence_text (
        original_statement,
        normalized_statement,
        context_rationale
    )
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


CREATE TABLE review_decisions (
    review_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL,
    entity_key VARCHAR(255) NOT NULL,
    decision_type VARCHAR(50) NOT NULL,
    previous_value JSON,
    new_value JSON,
    reviewer VARCHAR(255) NOT NULL,
    review_notes TEXT,
    reviewed_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


CREATE OR REPLACE VIEW v_need_summary AS
SELECT
    n.need_id,
    n.need_code,
    n.canonical_need,
    n.need_summary,
    n.need_category,
    n.desired_outcome,
    n.lifecycle_status,
    n.priority,
    n.trend,
    n.human_reviewed,
    n.reviewer,
    n.notes,

    COUNT(DISTINCT e.evidence_id) AS evidence_count,
    COUNT(DISTINCT e.source_id) AS source_count,
    COUNT(DISTINCT e.organization_id) AS organization_count,
    COUNT(DISTINCT e.event_year) AS year_count,

    MIN(e.event_year) AS first_seen_year,
    MAX(e.event_year) AS last_seen_year,

    LEAST(
        100,
        COUNT(DISTINCT e.evidence_id) * 1.5
        + COUNT(DISTINCT e.source_id) * 8
        + COUNT(DISTINCT e.organization_id) * 4
        + COUNT(DISTINCT e.event_year) * 5
    ) AS signal_score

FROM needs n

LEFT JOIN evidence e
    ON e.need_id = n.need_id
    AND e.duplicate_evidence = FALSE

GROUP BY
    n.need_id,
    n.need_code,
    n.canonical_need,
    n.need_summary,
    n.need_category,
    n.desired_outcome,
    n.lifecycle_status,
    n.priority,
    n.trend,
    n.human_reviewed,
    n.reviewer,
    n.notes;