param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("demo", "full")]
    [string]$Mode,
    [string]$DemoDatabase = "earthdata_insights_demo",
    [string]$ComposeFile = ".\docker_compose.yaml"
)

$ErrorActionPreference = "Stop"

function Read-DotEnvValue([string]$Name) {
    $line = Get-Content .env | Where-Object { $_ -match "^$Name=" } | Select-Object -First 1
    if (-not $line) { return $null }
    return ($line -replace "^$Name=", "").Trim()
}

function Set-DotEnvValue([string]$Name, [string]$Value) {
    $lines = @(Get-Content .env)
    $pattern = "^$Name="
    $found = $false
    $updated = foreach ($line in $lines) {
        if ($line -match $pattern) {
            $found = $true
            "$Name=$Value"
        } else {
            $line
        }
    }
    if (-not $found) { $updated += "$Name=$Value" }
    $updated | Set-Content .env -Encoding utf8
}

$fullDatabase = Read-DotEnvValue "MARIADB_DATABASE"
if (-not $fullDatabase) { throw "MARIADB_DATABASE is missing from .env" }

if ($Mode -eq "demo") {
    $targetDatabase = $DemoDatabase
    $datasetMode = "demo"
} else {
    $targetDatabase = $fullDatabase
    $datasetMode = "full"
}

Set-DotEnvValue "APP_DATABASE" $targetDatabase
Set-DotEnvValue "DATASET_MODE" $datasetMode

Write-Host "Switching application to $($datasetMode.ToUpper()) dataset..."
Write-Host "Database: $targetDatabase"

# Recreate only application containers. MariaDB and its volume remain untouched.
docker compose -f $ComposeFile up -d --no-deps --force-recreate api ui

Start-Sleep -Seconds 3

try {
    $health = Invoke-RestMethod http://127.0.0.1:8000/health
    Write-Host "API status: $($health.status)"
} catch {
    Write-Warning "API health check did not succeed yet. Check: docker logs --tail 100 uwg-api"
}

Write-Host "UI: http://127.0.0.1:8501"
