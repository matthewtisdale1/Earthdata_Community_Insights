$ErrorActionPreference = 'Stop'
Push-Location (Join-Path $PSScriptRoot '..')
try {
    # The checkout folder may have changed since the original stack was created.
    # Reuse the database container's Compose identity instead of creating a new stack.
    $composeArgs = @('compose')
    $databaseId = docker container ls -a --filter 'name=^/uwg-mariadb$' --format '{{.ID}}'
    if ($LASTEXITCODE -ne 0) { throw 'Cannot reach Docker. Start Docker Desktop and retry.' }

    if ($databaseId) {
        $labelsJson = docker inspect --format '{{json .Config.Labels}}' uwg-mariadb
        if ($LASTEXITCODE -ne 0) { throw 'Cannot inspect the existing database container.' }
        $labels = $labelsJson | ConvertFrom-Json
        $existingProject = $labels.'com.docker.compose.project'
        if (-not $existingProject -or $labels.'com.docker.compose.service' -ne 'mariadb') {
            throw 'uwg-mariadb is not a recognized Compose mariadb service. No containers were changed. Inspect its ownership before continuing.'
        }
        $composeArgs += @('--project-name', $existingProject)

        # Check that the resolved configuration will use the actual existing data volume.
        # Keep the full configuration in memory: it contains credentials, so never print it.
        $configJson = docker @composeArgs config --format json
        if ($LASTEXITCODE -ne 0) { throw 'Cannot resolve Docker Compose configuration.' }
        $config = $configJson | ConvertFrom-Json
        $mountsJson = docker inspect --format '{{json .Mounts}}' uwg-mariadb
        if ($LASTEXITCODE -ne 0) { throw 'Cannot inspect the existing database volume.' }
        $mounts = $mountsJson | ConvertFrom-Json
        $actualMount = @($mounts | Where-Object { $_.Destination -eq '/var/lib/mysql' })
        $configuredMount = @($config.services.mariadb.volumes | Where-Object { $_.target -eq '/var/lib/mysql' })
        if ($actualMount.Count -ne 1 -or $configuredMount.Count -ne 1) {
            throw 'Could not identify a unique database data mount. No containers were changed.'
        }
        if ($actualMount[0].Type -ne 'volume' -or $configuredMount[0].type -ne 'volume') {
            throw 'This script expects the existing database to use a named volume. No containers were changed.'
        }
        $volumeKey = $configuredMount[0].source
        $expectedVolume = $config.volumes.$volumeKey.name
        if (-not $expectedVolume -or $expectedVolume -ne $actualMount[0].Name) {
            throw "Database volume mismatch: Compose expects '$expectedVolume', but the existing container uses '$($actualMount[0].Name)'. No containers were changed."
        }

        foreach ($serviceName in @('api', 'ui')) {
            $containerName = "uwg-$serviceName"
            $serviceId = docker container ls -a --filter "name=^/$containerName$" --format '{{.ID}}'
            if ($LASTEXITCODE -ne 0) { throw "Cannot inspect $containerName." }
            if ($serviceId) {
                $serviceLabelsJson = docker inspect --format '{{json .Config.Labels}}' $containerName
                if ($LASTEXITCODE -ne 0) { throw "Cannot inspect $containerName ownership." }
                $serviceLabels = $serviceLabelsJson | ConvertFrom-Json
                if ($serviceLabels.'com.docker.compose.project' -ne $existingProject -or
                    $serviceLabels.'com.docker.compose.service' -ne $serviceName) {
                    throw "$containerName belongs to a different project or service. No containers were changed."
                }
            }
        }
        Write-Host "Reusing Compose project '$existingProject' and database volume '$expectedVolume'."
    }

    docker @composeArgs build api ui
    if ($LASTEXITCODE -ne 0) { throw 'Build failed' }
    docker @composeArgs up -d mariadb
    if ($LASTEXITCODE -ne 0) { throw 'Database startup failed' }
    docker @composeArgs run --rm api python -m app.migrate_planning
    if ($LASTEXITCODE -ne 0) { throw 'Planning migration failed; existing data was not reset' }
    docker @composeArgs up -d api ui
    if ($LASTEXITCODE -ne 0) { throw 'Application startup failed' }
    Write-Host 'Planning is ready at http://127.0.0.1:8501/planning'
    if ($existingProject) {
        Write-Host "For status: docker compose --project-name $existingProject ps"
    }
} finally { Pop-Location }
