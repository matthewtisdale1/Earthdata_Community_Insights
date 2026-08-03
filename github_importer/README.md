# GitHub artifact importer

The GitHub importer synchronizes approved repositories registered in `external_sources` into `implementation_artifacts`.

It currently imports:

- Issues
- Pull requests returned by the GitHub Issues API
- Releases
- Labels, milestones, author, timestamps, state, URL, and raw metadata

## Configuration

Set a read-only GitHub token in `.env`:

```dotenv
GITHUB_TOKEN=replace-with-a-read-only-token
```

Optional environment variables:

```dotenv
SOURCE_CODE=
FULL_SYNC=false
```

- `SOURCE_CODE` limits a run to one registered source, such as `GITHUB_NASA_HARMONY`.
- `FULL_SYNC=true` ignores the previous synchronization timestamp for issues and pull requests.

## Build

```powershell
docker compose -f .\docker_compose.yaml build github-importer
```

## Run all registered repositories

```powershell
docker compose -f .\docker_compose.yaml `
    --profile github-import `
    run --rm github-importer
```

## Run one repository

```powershell
$env:SOURCE_CODE = "GITHUB_NASA_HARMONY"

docker compose -f .\docker_compose.yaml `
    --profile github-import `
    run --rm github-importer

Remove-Item Env:SOURCE_CODE
```

## Reusing an existing MariaDB container

When MariaDB was created by another Compose project, connect it to this repository's Docker network with the `mariadb` alias before running the importer:

```powershell
docker network connect `
    --alias mariadb `
    earthdata_community_insights_default `
    uwg-mariadb
```

If the container is already connected, Docker reports that the endpoint already exists and no action is needed.

Run the importer without starting dependencies when reusing that database container:

```powershell
docker compose -f .\docker_compose.yaml build github-importer

docker compose -f .\docker_compose.yaml `
    --profile github-import `
    run --rm --no-deps github-importer
```

## Verify

```powershell
Invoke-RestMethod http://127.0.0.1:8000/tools |
    Format-Table tool_code, tool_name, issue_count, pull_request_count, release_count
```

Refresh the **Earthdata Tools** page after the import. Artifact totals and recent artifacts should populate.

## Important interpretation rule

A closed GitHub issue is not proof that a community need was solved. Imported artifacts remain implementation evidence candidates until a reviewer confirms their relationship to a need.
