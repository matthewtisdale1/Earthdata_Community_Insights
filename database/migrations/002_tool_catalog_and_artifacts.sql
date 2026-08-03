-- Earthdata Community Insights
-- Migration 002: tool catalog and implementation artifacts
--
-- This migration extends the workbook prototype without changing the existing
-- organizations, sources, needs, evidence, or review_decisions tables.

CREATE TABLE IF NOT EXISTS tools (
    tool_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    tool_code VARCHAR(60) NOT NULL UNIQUE,
    tool_name VARCHAR(255) NOT NULL,
    tool_type VARCHAR(100),
    owner_name VARCHAR(255),
    description TEXT,
    homepage_url TEXT,
    documentation_url TEXT,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_tools_active (active),
    INDEX idx_tools_name (tool_name)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


CREATE TABLE IF NOT EXISTS external_sources (
    external_source_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    source_code VARCHAR(100) NOT NULL UNIQUE,
    tool_id BIGINT UNSIGNED NOT NULL,
    source_kind VARCHAR(50) NOT NULL,
    owner_name VARCHAR(255),
    repository_name VARCHAR(255),
    base_url TEXT NOT NULL,
    api_url TEXT,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    sync_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    last_synced_at DATETIME,
    sync_cursor DATETIME,
    sync_status VARCHAR(50),
    sync_error TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_external_source_tool
        FOREIGN KEY (tool_id)
        REFERENCES tools(tool_id)
        ON DELETE CASCADE,

    INDEX idx_external_source_tool (tool_id),
    INDEX idx_external_source_kind (source_kind),
    INDEX idx_external_source_sync (sync_enabled, last_synced_at)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


CREATE TABLE IF NOT EXISTS implementation_artifacts (
    artifact_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    artifact_code VARCHAR(160) NOT NULL UNIQUE,
    external_source_id BIGINT UNSIGNED NOT NULL,
    tool_id BIGINT UNSIGNED NOT NULL,

    artifact_type VARCHAR(50) NOT NULL,
    external_id VARCHAR(255) NOT NULL,
    external_number BIGINT,
    title TEXT NOT NULL,
    body LONGTEXT,
    state VARCHAR(50),
    state_reason VARCHAR(100),

    author_name VARCHAR(255),
    labels_json JSON,
    milestone_name VARCHAR(255),

    external_url TEXT NOT NULL,
    created_external_at DATETIME,
    updated_external_at DATETIME,
    closed_external_at DATETIME,
    merged_external_at DATETIME,

    retrieved_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    content_hash CHAR(64),
    raw_metadata JSON,

    CONSTRAINT fk_artifact_source
        FOREIGN KEY (external_source_id)
        REFERENCES external_sources(external_source_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_artifact_tool
        FOREIGN KEY (tool_id)
        REFERENCES tools(tool_id)
        ON DELETE CASCADE,

    UNIQUE KEY uq_artifact_external (
        external_source_id,
        artifact_type,
        external_id
    ),

    INDEX idx_artifact_tool (tool_id),
    INDEX idx_artifact_type_state (artifact_type, state),
    INDEX idx_artifact_updated (updated_external_at),

    FULLTEXT INDEX ft_artifact_text (
        title,
        body
    )
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


CREATE TABLE IF NOT EXISTS artifact_relationships (
    source_artifact_id BIGINT UNSIGNED NOT NULL,
    target_artifact_id BIGINT UNSIGNED NOT NULL,
    relationship_type VARCHAR(80) NOT NULL,
    relationship_source VARCHAR(80),
    confidence DECIMAL(6,5),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (
        source_artifact_id,
        target_artifact_id,
        relationship_type
    ),

    CONSTRAINT fk_artifact_relationship_source
        FOREIGN KEY (source_artifact_id)
        REFERENCES implementation_artifacts(artifact_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_artifact_relationship_target
        FOREIGN KEY (target_artifact_id)
        REFERENCES implementation_artifacts(artifact_id)
        ON DELETE CASCADE
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


CREATE TABLE IF NOT EXISTS need_artifact_matches (
    match_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    need_id BIGINT UNSIGNED NOT NULL,
    artifact_id BIGINT UNSIGNED NOT NULL,

    relationship_type VARCHAR(80)
        NOT NULL DEFAULT 'Potential Match',

    lexical_score DECIMAL(6,5),
    semantic_score DECIMAL(6,5),
    metadata_score DECIMAL(6,5),
    overall_score DECIMAL(6,5),

    matched_terms JSON,
    match_explanation TEXT,
    match_method VARCHAR(100),
    matcher_version VARCHAR(100),

    review_status VARCHAR(40)
        NOT NULL DEFAULT 'Pending',
    reviewer VARCHAR(255),
    reviewed_at DATETIME,
    review_notes TEXT,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_match_need
        FOREIGN KEY (need_id)
        REFERENCES needs(need_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_match_artifact
        FOREIGN KEY (artifact_id)
        REFERENCES implementation_artifacts(artifact_id)
        ON DELETE CASCADE,

    UNIQUE KEY uq_need_artifact (
        need_id,
        artifact_id
    ),

    INDEX idx_match_need (need_id),
    INDEX idx_match_artifact (artifact_id),
    INDEX idx_match_review (review_status, overall_score)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


CREATE OR REPLACE VIEW v_tool_summary AS
SELECT
    t.tool_id,
    t.tool_code,
    t.tool_name,
    t.tool_type,
    t.owner_name,
    t.description,
    t.homepage_url,
    t.documentation_url,
    t.active,

    COUNT(DISTINCT es.external_source_id) AS source_count,
    COUNT(DISTINCT ia.artifact_id) AS artifact_count,

    COUNT(DISTINCT CASE
        WHEN ia.artifact_type = 'issue' THEN ia.artifact_id
    END) AS issue_count,

    COUNT(DISTINCT CASE
        WHEN ia.artifact_type = 'pull_request' THEN ia.artifact_id
    END) AS pull_request_count,

    COUNT(DISTINCT CASE
        WHEN ia.artifact_type = 'release' THEN ia.artifact_id
    END) AS release_count,

    MAX(es.last_synced_at) AS last_synced_at

FROM tools t
LEFT JOIN external_sources es
    ON es.tool_id = t.tool_id
LEFT JOIN implementation_artifacts ia
    ON ia.tool_id = t.tool_id
GROUP BY
    t.tool_id,
    t.tool_code,
    t.tool_name,
    t.tool_type,
    t.owner_name,
    t.description,
    t.homepage_url,
    t.documentation_url,
    t.active;


CREATE OR REPLACE VIEW v_need_implementation_summary AS
SELECT
    n.need_id,
    n.need_code,
    n.canonical_need,

    COUNT(DISTINCT nam.match_id) AS total_match_count,

    COUNT(DISTINCT CASE
        WHEN nam.review_status = 'Confirmed' THEN nam.match_id
    END) AS confirmed_match_count,

    COUNT(DISTINCT CASE
        WHEN nam.review_status = 'Pending' THEN nam.match_id
    END) AS pending_match_count,

    COUNT(DISTINCT CASE
        WHEN nam.relationship_type = 'Fully Addresses'
         AND nam.review_status = 'Confirmed'
        THEN nam.match_id
    END) AS fully_addressed_count,

    COUNT(DISTINCT CASE
        WHEN nam.relationship_type = 'Partially Addresses'
         AND nam.review_status = 'Confirmed'
        THEN nam.match_id
    END) AS partially_addressed_count

FROM needs n
LEFT JOIN need_artifact_matches nam
    ON nam.need_id = n.need_id
GROUP BY
    n.need_id,
    n.need_code,
    n.canonical_need;
