param(
    [string]$OutputPath = (Join-Path $env:USERPROFILE ("Downloads\ECI-current-knowledge-" + (Get-Date -Format 'yyyyMMdd-HHmmss') + ".json"))
)
$ErrorActionPreference = 'Stop'

# Read from the running API's selected database, regardless of Compose project.
# Only an explicit table allowlist is exported. Credentials are never included.
$exportCode = @'
import json
import os
import sys
from datetime import datetime, timezone
from sqlalchemy import create_engine, inspect, text

tables = (
    "needs", "evidence", "sources", "organizations", "review_decisions",
    "capabilities", "need_capabilities", "planning_teams", "planning_pis",
    "planning_work", "planning_history", "planning_outcomes"
)
try:
    engine = create_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
    with engine.connect() as connection:
        with connection.begin():
            available = set(inspect(connection).get_table_names())
            records = {
                table: [dict(row) for row in connection.execute(
                    text("SELECT * FROM " + table)
                ).mappings()]
                for table in tables if table in available
            }
    if not all(table in records for table in ("needs", "evidence", "sources")):
        raise ValueError("Missing required ECI tables")
    result = {
        "schema_version": 1,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "dataset_mode": os.environ.get("DATASET_MODE", "unspecified"),
        "purpose": "Read-only snapshot for reconciliation; not an import file",
        "missing_optional_tables": [table for table in tables if table not in available],
        "counts": {table: len(rows) for table, rows in records.items()},
        "tables": records,
    }
    print(json.dumps(result, default=str, ensure_ascii=True))
except Exception:
    print("Export failed. Check that uwg-api is running and its database is available.", file=sys.stderr)
    sys.exit(1)
'@

$exportJson = $exportCode | docker exec -i uwg-api python -
if ($LASTEXITCODE -ne 0) { throw 'Read-only export failed. No export file was written.' }
$jsonText = $exportJson -join [Environment]::NewLine
$snapshot = $jsonText | ConvertFrom-Json
if ($snapshot.schema_version -ne 1 -or $null -eq $snapshot.tables.needs) {
    throw 'The export did not contain the expected ECI snapshot.'
}
$resolvedPath = [System.IO.Path]::GetFullPath($OutputPath)
if (Test-Path -LiteralPath $resolvedPath) { throw "File already exists: $resolvedPath. Choose a new OutputPath." }
$parentPath = Split-Path -Parent $resolvedPath
if (-not (Test-Path -LiteralPath $parentPath)) {
    New-Item -ItemType Directory -Path $parentPath | Out-Null
}
[System.IO.File]::WriteAllText($resolvedPath, $jsonText, (New-Object System.Text.UTF8Encoding($false)))
Write-Host "Saved read-only snapshot: $resolvedPath"
Write-Host "Needs: $($snapshot.counts.needs); Evidence: $($snapshot.counts.evidence); Sources: $($snapshot.counts.sources)"
Write-Host 'Upload this JSON in the conversation for reconciliation. It contains your current records and review history.'
