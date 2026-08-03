param(
    [int]$ExampleCount = 2,
    [string[]]$NeedCodes = @(),
    [int]$MaxArtifactsPerNeed = 5,
    [string]$SourceDatabase = "",
    [string]$DemoDatabase = "earthdata_insights_demo"
)

$ErrorActionPreference = "Stop"

function Read-DotEnvValue([string]$Name) {
    $line = Get-Content .env |
        Where-Object { $_ -match "^$Name=" } |
        Select-Object -First 1

    if (-not $line) {
        throw "Missing $Name in .env"
    }

    return ($line -replace "^$Name=", "").Trim()
}

function Assert-LastCommand([string]$Description) {
    if ($LASTEXITCODE -ne 0) {
        throw "$Description failed with exit code $LASTEXITCODE."
    }
}

if ($ExampleCount -lt 1 -or $ExampleCount -gt 10) {
    throw "ExampleCount must be between 1 and 10."
}

if ($MaxArtifactsPerNeed -lt 1 -or $MaxArtifactsPerNeed -gt 25) {
    throw "MaxArtifactsPerNeed must be between 1 and 25."
}

$rootPassword = Read-DotEnvValue "MARIADB_ROOT_PASSWORD"
$appUser = Read-DotEnvValue "MARIADB_USER"

if (-not $SourceDatabase) {
    $SourceDatabase = Read-DotEnvValue "MARIADB_DATABASE"
}

if ($SourceDatabase -eq $DemoDatabase) {
    throw "Source and demo database names must be different."
}

$normalizedNeedCodes = @(
    $NeedCodes |
        ForEach-Object { $_.Trim().ToUpperInvariant() } |
        Where-Object { $_ } |
        Select-Object -Unique
)

$selectionDescription = if ($normalizedNeedCodes.Count -gt 0) {
    "curated need(s): $($normalizedNeedCodes -join ', ')"
}
else {
    "the top $ExampleCount automatically selected match(es)"
}

Write-Host "Creating demo database '$DemoDatabase' from '$SourceDatabase' using $selectionDescription..."

$createSql = @"
DROP DATABASE IF EXISTS ``$DemoDatabase``;
CREATE DATABASE ``$DemoDatabase``
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
GRANT ALL PRIVILEGES ON ``$DemoDatabase``.* TO '$appUser'@'%';
FLUSH PRIVILEGES;
"@

$createSql |
    docker exec -i -e MYSQL_PWD=$rootPassword uwg-mariadb `
    mariadb -uroot
Assert-LastCommand "Creating the demo database"

# Copy the full schema and data before selecting the curated records.
docker exec -e MYSQL_PWD=$rootPassword uwg-mariadb `
    sh -c "mariadb-dump -uroot --single-transaction --routines --triggers '$SourceDatabase' | mariadb -uroot '$DemoDatabase'"
Assert-LastCommand "Copying the full database into the demo database"

if ($normalizedNeedCodes.Count -gt 0) {
    $escapedCodes = $normalizedNeedCodes |
        ForEach-Object { "'" + $_.Replace("'", "''") + "'" }
    $needCodeList = $escapedCodes -join ", "

    $selectionSql = @"
CREATE TEMPORARY TABLE selected_needs AS
SELECT need_id
FROM needs
WHERE UPPER(need_code) IN ($needCodeList);

CREATE TEMPORARY TABLE ranked_matches AS
SELECT
    nam.match_id,
    nam.need_id,
    nam.artifact_id,
    ROW_NUMBER() OVER (
        PARTITION BY nam.need_id
        ORDER BY
            CASE nam.review_status
                WHEN 'Confirmed' THEN 0
                WHEN 'Uncertain' THEN 1
                WHEN 'Pending' THEN 2
                ELSE 3
            END,
            nam.overall_score DESC,
            nam.match_id
    ) AS match_rank
FROM need_artifact_matches nam
JOIN selected_needs sn
  ON sn.need_id = nam.need_id;

CREATE TEMPORARY TABLE selected_matches AS
SELECT match_id, need_id, artifact_id
FROM ranked_matches
WHERE match_rank <= $MaxArtifactsPerNeed;
"@
}
else {
    $selectionSql = @"
CREATE TEMPORARY TABLE selected_matches AS
SELECT match_id, need_id, artifact_id
FROM need_artifact_matches
ORDER BY
    CASE review_status
        WHEN 'Confirmed' THEN 0
        WHEN 'Uncertain' THEN 1
        WHEN 'Pending' THEN 2
        ELSE 3
    END,
    overall_score DESC,
    match_id
LIMIT $ExampleCount;

CREATE TEMPORARY TABLE selected_needs AS
SELECT DISTINCT need_id
FROM selected_matches;
"@
}

$pruneSql = @"
USE ``$DemoDatabase``;

$selectionSql

CREATE TEMPORARY TABLE selected_artifacts AS
SELECT DISTINCT artifact_id
FROM selected_matches;

SET @selected_need_count = (SELECT COUNT(*) FROM selected_needs);

DELETE FROM need_artifact_matches
WHERE match_id NOT IN (
    SELECT match_id FROM selected_matches
);

DELETE FROM artifact_relationships
WHERE source_artifact_id NOT IN (
        SELECT artifact_id FROM selected_artifacts
    )
   OR target_artifact_id NOT IN (
        SELECT artifact_id FROM selected_artifacts
    );

DELETE FROM implementation_artifacts
WHERE artifact_id NOT IN (
    SELECT artifact_id FROM selected_artifacts
);

-- Evidence is a child of needs, so remove evidence for unselected needs first.
DELETE FROM evidence
WHERE need_id NOT IN (
    SELECT need_id FROM selected_needs
);

DELETE FROM needs
WHERE need_id NOT IN (
    SELECT need_id FROM selected_needs
);

DELETE es
FROM external_sources es
LEFT JOIN implementation_artifacts ia
  ON ia.external_source_id = es.external_source_id
WHERE ia.artifact_id IS NULL;

DELETE t
FROM tools t
LEFT JOIN implementation_artifacts ia
  ON ia.tool_id = t.tool_id
WHERE ia.artifact_id IS NULL;

DELETE o
FROM organizations o
LEFT JOIN evidence e
  ON e.organization_id = o.organization_id
WHERE e.evidence_id IS NULL;

DELETE s
FROM sources s
LEFT JOIN evidence e
  ON e.source_id = s.source_id
WHERE e.evidence_id IS NULL;

DELETE FROM review_decisions;

SELECT
    (SELECT COUNT(*) FROM needs) AS needs,
    (SELECT COUNT(*) FROM evidence) AS evidence,
    (SELECT COUNT(*) FROM sources) AS sources,
    (SELECT COUNT(*) FROM organizations) AS organizations,
    (SELECT COUNT(*) FROM implementation_artifacts) AS artifacts,
    (SELECT COUNT(*) FROM need_artifact_matches) AS matches,
    (SELECT COUNT(*) FROM tools) AS tools;
"@

$pruneSql |
    docker exec -i -e MYSQL_PWD=$rootPassword uwg-mariadb `
    mariadb -uroot
Assert-LastCommand "Pruning the demo database"

if ($normalizedNeedCodes.Count -gt 0) {
    $verifyCodes = $normalizedNeedCodes -join ", "
    Write-Host "Curated demo needs requested: $verifyCodes"
}

Write-Host ""
Write-Host "Demo database refreshed successfully."
Write-Host "Switch to it with: .\scripts\use-dataset.ps1 demo"
