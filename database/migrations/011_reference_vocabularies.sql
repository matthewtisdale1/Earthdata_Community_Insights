CREATE TABLE IF NOT EXISTS reference_vocabularies (
    vocabulary_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    vocabulary_type VARCHAR(50) NOT NULL,
    item_code VARCHAR(100) NOT NULL,
    item_name VARCHAR(255) NOT NULL,
    description TEXT,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    sort_order INT NOT NULL DEFAULT 0,
    vocabulary_version VARCHAR(30) NOT NULL DEFAULT '1',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT uq_reference_vocabulary UNIQUE (vocabulary_type, item_code),
    INDEX idx_reference_vocabulary_type (vocabulary_type, active, sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
