# Earthdata Community Insights

Earthdata Community Insights is a prototype platform for identifying, organizing, and analyzing recurring needs expressed by the NASA Earthdata community.

The application connects community needs to supporting evidence and is being extended to identify related capabilities, Earthdata tools, GitHub issues, pull requests, releases, and documentation.

## Questions the project is designed to answer

- What needs are being heard most often from the Earthdata community?
- Which needs recur across multiple organizations, communities, reports, and years?
- What source evidence supports each need?
- Which Earthdata tools or services may already address a need?
- Are related implementation tickets open, planned, partially implemented, or complete?
- Which high-signal needs still lack an identified solution?

## Current prototype

The current prototype provides:

- A MariaDB system of record
- A FastAPI REST API
- A Streamlit user interface
- Docker Compose for local development
- Import of structured community-needs data from an Excel workbook
- Search and filtering across needs and evidence
- Need-detail and evidence-detail views
- Human review and validation fields
- Organization and source views
- Signal scoring based on recurrence and source diversity

## Initial Earthdata tool scope

The first implementation-artifact integrations will focus on:

- Earthdata Search
- Worldview
- Global Imagery Browse Services (GIBS)
- Common Metadata Repository (CMR)
- Harmony

The planned GitHub integration will ingest issues, pull requests, releases, and related implementation artifacts from approved repositories, then propose links between those artifacts and canonical user needs.

## Core data model

```text
One canonical need
        │
        ├── supported by many evidence records
        ├── expressed by multiple organizations
        ├── associated with user communities
        ├── related to Earthdata capabilities
        └── linked to implementation artifacts
```

Implementation artifacts may include:

- GitHub issues
- Pull requests
- Releases
- Documentation
- Roadmap items
- Tool features
- Service endpoints

A closed issue is not automatically treated as a solved need. Human review is required to determine whether an artifact tracks, proposes, partially addresses, fully addresses, implements, documents, or is unrelated to a need.

## Architecture

```text
Browser
   │
   ▼
Streamlit UI
   │ REST / JSON
   ▼
FastAPI
   │ SQL
   ▼
MariaDB
```

Batch components extend the core application:

```text
UWG workbook
    │
    ▼
Workbook importer
    │
    ▼
MariaDB

GitHub repositories
    │
    ▼
GitHub importer
    │
    ▼
Implementation artifacts
    │
    ▼
Matching engine
    │
    ▼
Human review queue
```

## Local-to-NGAP mapping

| Local prototype | Future AWS NGAP implementation |
|---|---|
| Docker Compose | ECS/Fargate |
| MariaDB container | Amazon RDS for MariaDB |
| Local data directory | Amazon S3 |
| Batch importer container | ECS task |
| `.env` secrets | AWS Secrets Manager |
| Container logs | Amazon CloudWatch |
| Local browser access | NGAP-approved ingress and identity |

## Repository structure

```text
Earthdata_Community_Insights/
├── api/                  # FastAPI application
├── ui/                   # Streamlit user interface
├── importer/             # Workbook importer
├── github_importer/      # Planned GitHub synchronization worker
├── matcher/              # Planned need-to-artifact matcher
├── database/             # Schema, migrations, and seed data
├── data/                 # Local source data; excluded from Git
├── docs/                 # Architecture and project documentation
├── tests/                # Automated tests
├── compose.yaml          # Local Docker Compose stack
├── .env.example          # Required environment-variable template
└── README.md
```

Some planned folders may not yet exist.

## Local requirements

Install:

- Git
- Docker Desktop
- Docker Compose
- A modern web browser

On Windows, Docker Desktop should use the WSL 2 backend.

Verify Docker:

```powershell
docker version
docker compose version
docker run --rm hello-world
```

## Local setup

### 1. Clone the repository

```powershell
git clone https://github.com/matthewtisdale1/Earthdata_Community_Insights.git
Set-Location Earthdata_Community_Insights
```

### 2. Create the local environment file

```powershell
Copy-Item .env.example .env
notepad .env
```

Example values:

```dotenv
MARIADB_DATABASE=earthdata_user_needs
MARIADB_USER=uwg_app
MARIADB_PASSWORD=change-this-local-password
MARIADB_ROOT_PASSWORD=change-this-root-password
GITHUB_TOKEN=replace-with-a-read-only-token
```

Never commit `.env` or real credentials. The repository includes `.env.example` only as a template.

### 3. Add the source workbook

Place the workbook in the local `data` directory using the filename expected by the importer. Source workbooks are intentionally excluded from Git unless a sanitized sample is provided.

### 4. Build and start the application

```powershell
docker compose up --build -d
docker compose ps
```

### 5. Import the workbook

```powershell
docker compose --profile import run --rm importer
```

### 6. Open the application

- Streamlit UI: `http://127.0.0.1:8501`
- FastAPI documentation: `http://127.0.0.1:8000/docs`
- Health endpoint: `http://127.0.0.1:8000/health`

Use `127.0.0.1` rather than `localhost` if workstation or browser security policies interfere with Streamlit JavaScript modules.

## Useful commands

Start services:

```powershell
docker compose up -d
```

Rebuild services:

```powershell
docker compose up --build -d
```

View logs:

```powershell
docker compose logs -f
```

Stop services while preserving data:

```powershell
docker compose down
```

Delete the local database volume and start over:

```powershell
docker compose down -v
docker compose up --build -d
docker compose --profile import run --rm importer
```

## Planned GitHub artifact workflow

```powershell
docker compose --profile github-import run --rm github-importer
docker compose --profile match run --rm matcher
docker compose up -d
```

The GitHub importer will retrieve implementation artifacts from approved repositories. The matcher will create candidate links between needs and artifacts. A reviewer will then confirm, change, or reject each proposed relationship.

## Review principles

1. Preserve original source evidence.
2. Allow canonical needs to be refined during human review.
3. Treat automated clustering and matching results as draft hypotheses.
4. Do not infer implementation status solely from a GitHub issue state.
5. Require explicit human confirmation for implementation claims.
6. Keep every relationship traceable to its source evidence.

## Roadmap

### Version 0.1 — Workbook prototype

- Import UWG report information
- Browse canonical needs
- Review supporting evidence
- Edit and validate needs
- Rank recurring needs

### Version 0.2 — Earthdata tool catalog

- Register Earthdata Search
- Register Worldview
- Register GIBS
- Register CMR
- Register Harmony
- Associate approved repositories and documentation sources

### Version 0.3 — GitHub artifact ingestion

- Import issues
- Import pull requests
- Import releases
- Track synchronization status

### Version 0.4 — Need-to-artifact matching

- Generate lexical candidate matches
- Review candidate links
- Classify implementation relationships
- Identify needs without solutions

### Version 0.5 — NGAP pilot

- Deploy services to ECS/Fargate
- Move MariaDB to Amazon RDS
- Store source documents in S3
- Use Secrets Manager and CloudWatch
- Integrate NGAP-approved identity and ingress

## Project status

This repository is currently a prototype and research effort. Extracted needs, automated clusters, signal scores, and implementation matches should not be treated as authoritative program decisions without review.

## Contributing

Contributions should:

- Preserve source traceability
- Avoid committing secrets or restricted data
- Include database migrations for schema changes
- Include clear testing instructions
- Keep automated matches distinguishable from human-confirmed relationships

A formal contributing guide will be added as the project matures.

## License

See the repository `LICENSE` file once a project license is selected.
