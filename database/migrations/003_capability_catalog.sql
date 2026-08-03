-- Migration 003: first-class Earthdata capability catalog

CREATE TABLE IF NOT EXISTS capabilities (
    capability_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    capability_code VARCHAR(80) NOT NULL UNIQUE,
    capability_name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    description TEXT,
    keywords_json JSON,
    maturity VARCHAR(50) NOT NULL DEFAULT 'Established',
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_capability_category (category),
    INDEX idx_capability_name (capability_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS tool_capabilities (
    tool_id BIGINT UNSIGNED NOT NULL,
    capability_id BIGINT UNSIGNED NOT NULL,
    support_level VARCHAR(50) NOT NULL DEFAULT 'Supported',
    evidence_source VARCHAR(100),
    notes TEXT,
    reviewed BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (tool_id, capability_id),
    CONSTRAINT fk_tool_cap_tool FOREIGN KEY (tool_id) REFERENCES tools(tool_id) ON DELETE CASCADE,
    CONSTRAINT fk_tool_cap_capability FOREIGN KEY (capability_id) REFERENCES capabilities(capability_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS need_capabilities (
    need_id BIGINT UNSIGNED NOT NULL,
    capability_id BIGINT UNSIGNED NOT NULL,
    relationship_type VARCHAR(80) NOT NULL DEFAULT 'Requires',
    confidence DECIMAL(6,5),
    match_method VARCHAR(100),
    review_status VARCHAR(40) NOT NULL DEFAULT 'Pending',
    reviewer VARCHAR(255),
    review_notes TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (need_id, capability_id),
    CONSTRAINT fk_need_cap_need FOREIGN KEY (need_id) REFERENCES needs(need_id) ON DELETE CASCADE,
    CONSTRAINT fk_need_cap_capability FOREIGN KEY (capability_id) REFERENCES capabilities(capability_id) ON DELETE CASCADE,
    INDEX idx_need_cap_review (review_status, confidence)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO capabilities (capability_code, capability_name, category, description, keywords_json) VALUES
('SPATIAL_SUBSETTING','Spatial Subsetting','Data Transformation','Extract data for a geographic area, bounding box, polygon, or shape.', JSON_ARRAY('spatial subset','bounding box','bbox','polygon','shape','crop','clip','hoss')),
('VARIABLE_SUBSETTING','Variable Subsetting','Data Transformation','Select specific variables, bands, or fields from a data product.', JSON_ARRAY('variable subset','variables','bands','fields','var subsetter')),
('TEMPORAL_SUBSETTING','Temporal Subsetting','Data Transformation','Extract data for a selected date or time range.', JSON_ARRAY('temporal subset','time range','date range')),
('REFORMATTING','Reformatting','Data Transformation','Convert data into another supported file format.', JSON_ARRAY('reformat','format conversion','netcdf','geotiff','zarr')),
('REPROJECTION','Reprojection','Data Transformation','Transform data into another coordinate reference system or map projection.', JSON_ARRAY('reproject','projection','crs','epsg')),
('CONCATENATION','Concatenation','Data Transformation','Combine multiple inputs or outputs into a consolidated result.', JSON_ARRAY('concatenate','aggregate','combine','merge granules')),
('SPATIAL_SEARCH','Spatial Search','Discovery','Discover data using a point, bounding box, polygon, or other spatial constraint.', JSON_ARRAY('spatial search','bounding box search','polygon search','geometry')),
('TEMPORAL_SEARCH','Temporal Search','Discovery','Discover data using date and time constraints.', JSON_ARRAY('temporal search','time search','date search')),
('KEYWORD_SEARCH','Keyword Search','Discovery','Discover collections and granules through free-text or controlled keyword search.', JSON_ARRAY('keyword search','free text','faceted search')),
('VISUALIZATION','Visualization','Analysis and Visualization','Interactively view and explore Earth observation data.', JSON_ARRAY('visualize','map','browse imagery','animation')),
('IMAGE_TILES','Image Tiles','Access and Delivery','Deliver map imagery through tiled services.', JSON_ARRAY('tiles','wmts','wms','gibs')),
('DATA_DOWNLOAD','Data Download','Access and Delivery','Download original or processed Earth science data.', JSON_ARRAY('download','delivery','access data')),
('ASYNC_PROCESSING','Asynchronous Processing','Processing','Run long-duration data operations as jobs with status and result tracking.', JSON_ARRAY('async','job status','background processing','workflow')),
('STAC_ACCESS','STAC Access','Standards and APIs','Expose or consume SpatioTemporal Asset Catalog resources.', JSON_ARRAY('stac','catalog','items','collections')),
('OGC_API','OGC API','Standards and APIs','Provide standards-based OGC web API access.', JSON_ARRAY('ogc api','coverages','features'))
ON DUPLICATE KEY UPDATE capability_name=VALUES(capability_name), category=VALUES(category), description=VALUES(description), keywords_json=VALUES(keywords_json);

-- Initial curated tool-capability mappings for the five prototype tools.
INSERT IGNORE INTO tool_capabilities (tool_id, capability_id, support_level, evidence_source, reviewed)
SELECT t.tool_id, c.capability_id, 'Supported', 'Curated prototype seed', TRUE
FROM tools t JOIN capabilities c
WHERE (t.tool_code='HARMONY' AND c.capability_code IN ('SPATIAL_SUBSETTING','VARIABLE_SUBSETTING','TEMPORAL_SUBSETTING','REFORMATTING','REPROJECTION','CONCATENATION','ASYNC_PROCESSING','OGC_API','STAC_ACCESS','DATA_DOWNLOAD'))
   OR (t.tool_code='CMR' AND c.capability_code IN ('SPATIAL_SEARCH','TEMPORAL_SEARCH','KEYWORD_SEARCH','STAC_ACCESS','OGC_API'))
   OR (t.tool_code='EARTHDATA_SEARCH' AND c.capability_code IN ('SPATIAL_SEARCH','TEMPORAL_SEARCH','KEYWORD_SEARCH','DATA_DOWNLOAD'))
   OR (t.tool_code='WORLDVIEW' AND c.capability_code IN ('SPATIAL_SEARCH','TEMPORAL_SEARCH','VISUALIZATION','DATA_DOWNLOAD'))
   OR (t.tool_code='GIBS' AND c.capability_code IN ('VISUALIZATION','IMAGE_TILES','OGC_API'));

-- Curated demonstration link for NEED-0042.
INSERT INTO need_capabilities (need_id, capability_id, relationship_type, confidence, match_method, review_status, reviewer, review_notes)
SELECT n.need_id, c.capability_id, 'Requires', 1.00000, 'curated', 'Confirmed', 'prototype-seed', 'Explicitly curated for the NEED-0042 subsetting demonstration.'
FROM needs n JOIN capabilities c ON c.capability_code IN ('SPATIAL_SUBSETTING','VARIABLE_SUBSETTING','TEMPORAL_SUBSETTING')
WHERE n.need_code='NEED-0042'
ON DUPLICATE KEY UPDATE confidence=VALUES(confidence), review_status=VALUES(review_status), review_notes=VALUES(review_notes);

CREATE OR REPLACE VIEW v_capability_summary AS
SELECT c.capability_id, c.capability_code, c.capability_name, c.category, c.description, c.maturity, c.active,
       COUNT(DISTINCT nc.need_id) AS need_count,
       COUNT(DISTINCT e.evidence_id) AS evidence_count,
       COUNT(DISTINCT e.organization_id) AS organization_count,
       COUNT(DISTINCT tc.tool_id) AS tool_count,
       COUNT(DISTINCT CASE WHEN nc.review_status='Confirmed' THEN nc.need_id END) AS confirmed_need_count
FROM capabilities c
LEFT JOIN need_capabilities nc ON nc.capability_id=c.capability_id
LEFT JOIN evidence e ON e.need_id=nc.need_id
LEFT JOIN tool_capabilities tc ON tc.capability_id=c.capability_id
GROUP BY c.capability_id, c.capability_code, c.capability_name, c.category, c.description, c.maturity, c.active;
