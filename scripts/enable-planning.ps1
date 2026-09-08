$ErrorActionPreference = 'Stop'
Push-Location (Join-Path $PSScriptRoot '..')
try {
    docker compose build api ui
    if ($LASTEXITCODE -ne 0) { throw 'Build failed' }
    docker compose up -d mariadb
    if ($LASTEXITCODE -ne 0) { throw 'Database startup failed' }
    docker compose run --rm api python -m app.migrate_planning
    if ($LASTEXITCODE -ne 0) { throw 'Planning migration failed; existing data was not reset' }
    docker compose up -d api ui
    if ($LASTEXITCODE -ne 0) { throw 'Application startup failed' }
    Write-Host 'Planning is ready at http://127.0.0.1:8501/planning'
} finally { Pop-Location }
