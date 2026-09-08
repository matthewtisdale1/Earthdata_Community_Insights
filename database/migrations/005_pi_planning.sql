-- Additive and safe to re-run. Original need/evidence statuses remain intact.
CREATE TABLE IF NOT EXISTS planning_teams (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 name VARCHAR(200) NOT NULL UNIQUE, kind VARCHAR(30) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
CREATE TABLE IF NOT EXISTS planning_pis (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 name VARCHAR(100) NOT NULL UNIQUE, starts DATE NOT NULL, ends DATE NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
CREATE TABLE IF NOT EXISTS planning_work (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 need_id BIGINT UNSIGNED NOT NULL, title VARCHAR(500) NOT NULL, acceptance TEXT NOT NULL,
 team_id BIGINT UNSIGNED NULL, pi_id BIGINT UNSIGNED NULL,
 status VARCHAR(30) NOT NULL DEFAULT 'Backlog', delivery_link TEXT NOT NULL,
 evidence TEXT NOT NULL, version INT NOT NULL DEFAULT 1,
 FOREIGN KEY (need_id) REFERENCES needs(need_id),
 FOREIGN KEY (team_id) REFERENCES planning_teams(id),
 FOREIGN KEY (pi_id) REFERENCES planning_pis(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
CREATE TABLE IF NOT EXISTS planning_outcomes (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY, need_id BIGINT UNSIGNED NOT NULL,
 status VARCHAR(30) NOT NULL, evidence TEXT NOT NULL, reviewer VARCHAR(200) NOT NULL,
 assessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY (need_id) REFERENCES needs(need_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
CREATE TABLE IF NOT EXISTS planning_history (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY, entity_type VARCHAR(50) NOT NULL,
 entity_key VARCHAR(40) NOT NULL, previous_value LONGTEXT, new_value LONGTEXT NOT NULL,
 reviewer VARCHAR(200) NOT NULL, reason TEXT NOT NULL,
 changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 INDEX planning_history_entity (entity_type,entity_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ASSET roster supplied by the product owner. No DAAC mapping is implied.
-- Re-running setup adds missing teams without replacing existing records or assignments.
INSERT INTO planning_teams (name, kind)
SELECT 'Atmosphere', 'ASSET'
WHERE NOT EXISTS (SELECT 1 FROM planning_teams WHERE name = 'Atmosphere');
INSERT INTO planning_teams (name, kind)
SELECT 'Hydrosphere', 'ASSET'
WHERE NOT EXISTS (SELECT 1 FROM planning_teams WHERE name = 'Hydrosphere');
INSERT INTO planning_teams (name, kind)
SELECT 'Cryosphere', 'ASSET'
WHERE NOT EXISTS (SELECT 1 FROM planning_teams WHERE name = 'Cryosphere');
INSERT INTO planning_teams (name, kind)
SELECT 'Biosphere', 'ASSET'
WHERE NOT EXISTS (SELECT 1 FROM planning_teams WHERE name = 'Biosphere');
INSERT INTO planning_teams (name, kind)
SELECT 'Geosphere', 'ASSET'
WHERE NOT EXISTS (SELECT 1 FROM planning_teams WHERE name = 'Geosphere');
INSERT INTO planning_teams (name, kind)
SELECT 'XASSET (Cross Asset)', 'ASSET'
WHERE NOT EXISTS (SELECT 1 FROM planning_teams WHERE name = 'XASSET (Cross Asset)');
