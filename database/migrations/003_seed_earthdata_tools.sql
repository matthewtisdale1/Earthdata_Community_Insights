-- Earthdata Community Insights
-- Migration 003: seed the initial Earthdata tool catalog
--
-- Initial scope:
--   Earthdata Search, Worldview, GIBS, CMR, and Harmony.

INSERT INTO tools (
    tool_code,
    tool_name,
    tool_type,
    owner_name,
    description,
    homepage_url,
    documentation_url
)
VALUES
(
    'EARTHDATA_SEARCH',
    'Earthdata Search',
    'Web Application',
    'NASA Earthdata',
    'Earth science data discovery, search, visualization, comparison, and access.',
    'https://search.earthdata.nasa.gov',
    'https://www.earthdata.nasa.gov/learn/find-data/earthdata-search'
),
(
    'WORLDVIEW',
    'Worldview',
    'Web Application',
    'NASA GIBS',
    'Interactive browsing and visualization of global satellite imagery.',
    'https://worldview.earthdata.nasa.gov',
    'https://www.earthdata.nasa.gov/learn/find-data/near-real-time/worldview'
),
(
    'GIBS',
    'Global Imagery Browse Services',
    'Web Service',
    'NASA GIBS',
    'Standardized services that provide NASA Earth science imagery and map tiles.',
    'https://www.earthdata.nasa.gov/eosdis/science-system-description/eosdis-components/gibs',
    'https://nasa-gibs.github.io/gibs-api-docs/'
),
(
    'CMR',
    'Common Metadata Repository',
    'Metadata Service',
    'NASA Earthdata',
    'Repository and search services for NASA EOSDIS Earth science metadata.',
    'https://cmr.earthdata.nasa.gov',
    'https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html'
),
(
    'HARMONY',
    'Harmony',
    'Data Transformation Service',
    'NASA Earthdata',
    'Cloud-based services for transforming and accessing Earth observation data.',
    'https://harmony.earthdata.nasa.gov',
    'https://harmony.earthdata.nasa.gov/docs/'
)
ON DUPLICATE KEY UPDATE
    tool_name = VALUES(tool_name),
    tool_type = VALUES(tool_type),
    owner_name = VALUES(owner_name),
    description = VALUES(description),
    homepage_url = VALUES(homepage_url),
    documentation_url = VALUES(documentation_url),
    active = TRUE;


INSERT INTO external_sources (
    source_code,
    tool_id,
    source_kind,
    owner_name,
    repository_name,
    base_url,
    api_url
)
SELECT
    'GITHUB_NASA_EARTHDATA_SEARCH',
    tool_id,
    'github_repository',
    'nasa',
    'earthdata-search',
    'https://github.com/nasa/earthdata-search',
    'https://api.github.com/repos/nasa/earthdata-search'
FROM tools
WHERE tool_code = 'EARTHDATA_SEARCH'

UNION ALL

SELECT
    'GITHUB_NASA_GIBS_WORLDVIEW',
    tool_id,
    'github_repository',
    'nasa-gibs',
    'worldview',
    'https://github.com/nasa-gibs/worldview',
    'https://api.github.com/repos/nasa-gibs/worldview'
FROM tools
WHERE tool_code = 'WORLDVIEW'

UNION ALL

SELECT
    'GITHUB_NASA_GIBS_ONEARTH',
    tool_id,
    'github_repository',
    'nasa-gibs',
    'onearth',
    'https://github.com/nasa-gibs/onearth',
    'https://api.github.com/repos/nasa-gibs/onearth'
FROM tools
WHERE tool_code = 'GIBS'

UNION ALL

SELECT
    'GITHUB_NASA_GIBS_API_DOCS',
    tool_id,
    'github_repository',
    'nasa-gibs',
    'gibs-api-docs',
    'https://github.com/nasa-gibs/gibs-api-docs',
    'https://api.github.com/repos/nasa-gibs/gibs-api-docs'
FROM tools
WHERE tool_code = 'GIBS'

UNION ALL

SELECT
    'GITHUB_NASA_CMR',
    tool_id,
    'github_repository',
    'nasa',
    'Common-Metadata-Repository',
    'https://github.com/nasa/Common-Metadata-Repository',
    'https://api.github.com/repos/nasa/Common-Metadata-Repository'
FROM tools
WHERE tool_code = 'CMR'

UNION ALL

SELECT
    'GITHUB_NASA_HARMONY',
    tool_id,
    'github_repository',
    'nasa',
    'harmony',
    'https://github.com/nasa/harmony',
    'https://api.github.com/repos/nasa/harmony'
FROM tools
WHERE tool_code = 'HARMONY'

ON DUPLICATE KEY UPDATE
    tool_id = VALUES(tool_id),
    source_kind = VALUES(source_kind),
    owner_name = VALUES(owner_name),
    repository_name = VALUES(repository_name),
    base_url = VALUES(base_url),
    api_url = VALUES(api_url),
    active = TRUE,
    sync_enabled = TRUE;
