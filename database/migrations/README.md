# Database migrations

The initial database schema is created from `database/init/001_schema.sql` when MariaDB starts with an empty data volume.

Files in this directory extend an existing prototype database. They are intentionally separate from the initial schema because Docker's MariaDB initialization scripts run only when the database volume is first created.

## Apply migrations locally

Run these commands from the repository root in PowerShell after the MariaDB container is healthy.

```powershell
$rootPassword = (
    Get-Content .env |
    Where-Object { $_ -like 'MARIADB_ROOT_PASSWORD=*' }
) -replace 'MARIADB_ROOT_PASSWORD=', ''

$databaseName = (
    Get-Content .env |
    Where-Object { $_ -like 'MARIADB_DATABASE=*' }
) -replace 'MARIADB_DATABASE=', ''

Get-Content .\database\migrations\002_tool_catalog_and_artifacts.sql -Raw |
    docker compose exec -T mariadb `
    mariadb -uroot "-p$rootPassword" $databaseName

Get-Content .\database\migrations\003_seed_earthdata_tools.sql -Raw |
    docker compose exec -T mariadb `
    mariadb -uroot "-p$rootPassword" $databaseName
```

## Verify

```powershell
$appUser = (
    Get-Content .env |
    Where-Object { $_ -like 'MARIADB_USER=*' }
) -replace 'MARIADB_USER=', ''

$appPassword = (
    Get-Content .env |
    Where-Object { $_ -like 'MARIADB_PASSWORD=*' }
) -replace 'MARIADB_PASSWORD=', ''

$databaseName = (
    Get-Content .env |
    Where-Object { $_ -like 'MARIADB_DATABASE=*' }
) -replace 'MARIADB_DATABASE=', ''

docker compose exec mariadb mariadb `
    "-u$appUser" `
    "-p$appPassword" `
    $databaseName `
    -e "SELECT tool_code, tool_name FROM tools ORDER BY tool_name;"
```

Expected initial tools:

- Common Metadata Repository
- Earthdata Search
- Global Imagery Browse Services
- Harmony
- Worldview

## Migration principles

- Migrations must be safe to run against an existing local prototype database.
- New seed scripts should use upserts where practical.
- Existing source evidence must not be rewritten by implementation-intelligence migrations.
- Schema changes should be accompanied by verification commands and rollback notes when destructive changes are introduced.
- Real credentials must never be included in migration files or documentation.

## Current sequence

| Migration | Purpose |
|---|---|
| `002_tool_catalog_and_artifacts.sql` | Adds tools, external sources, implementation artifacts, artifact relationships, candidate matches, and summary views. |
| `003_seed_earthdata_tools.sql` | Seeds Earthdata Search, Worldview, GIBS, CMR, Harmony, and their initial approved GitHub repositories. |
