# Architecture

## Overview

Earthdata Community Insights is a containerized prototype for consolidating community needs, preserving their supporting evidence, and connecting those needs to implementation activity across Earthdata tools.

The current application uses a three-tier architecture:

```text
Browser
   │ HTTP
   ▼
Streamlit UI
   │ REST / JSON
   ▼
FastAPI
   │ SQL
   ▼
MariaDB
```

Batch ingestion extends this core without changing the interactive request path:

```text
UWG workbook ──► Workbook importer ──► MariaDB

Approved GitHub repositories ──► GitHub importer ──► Implementation artifacts
                                                        │
Canonical needs ─────────────────► Matching worker ◄────┘
                                      │
                                      ▼
                              Candidate match queue
                                      │
                                      ▼
                                Human review
```

## Current components

### Streamlit UI

The Streamlit application provides the interactive user experience for:

- Community-signal dashboards
- Need browsing and filtering
- Need details and review
- Evidence browsing and details
- Organization and source views
- Review queues

Navigation is centralized so detail pages can preserve the selected need or evidence record across page transitions.

### FastAPI service

FastAPI provides the application boundary between the UI and database. It is responsible for:

- Querying needs, evidence, organizations, and sources
- Returning dashboard summaries
- Loading detail records
- Applying human review updates
- Exposing future tool, artifact, and match-review endpoints

The API should contain business rules that must remain consistent across user interfaces or future clients.

### MariaDB

MariaDB is the system of record. The initial schema contains:

- `organizations`
- `sources`
- `needs`
- `evidence`
- `review_decisions`
- `v_need_summary`

A canonical need can be supported by many evidence records. Evidence retains original wording and source traceability, while the canonical need can be refined through review.

### Workbook importer

The workbook importer is a repeatable batch process that reads structured source sheets and upserts records into MariaDB using stable identifiers. It is run separately from the long-running UI and API services.

## Planned implementation-intelligence components

### Tool catalog

The tool catalog will initially register:

- Earthdata Search
- Worldview
- GIBS
- CMR
- Harmony

Each tool can have one or more approved external sources, including GitHub repositories, documentation sites, and release feeds.

### GitHub importer

The GitHub importer will run as a batch container and retrieve approved public implementation artifacts such as:

- Issues
- Pull requests
- Releases
- Labels and milestones
- Relevant relationship metadata

The importer will persist source identifiers, URLs, timestamps, state, and raw metadata so records can be refreshed without losing traceability.

### Matching worker

The first matcher will use deterministic lexical and metadata scoring to identify candidate links between canonical needs and implementation artifacts. Semantic matching may be added later, after enough human-reviewed examples exist to evaluate it.

Automated matches are hypotheses, not implementation claims.

### Human match review

Reviewers will be able to confirm, reclassify, reject, or defer candidate links. Relationship types will distinguish between artifacts that:

- Track a need
- Propose a solution
- Partially address a need
- Fully address a need
- Implement a capability
- Document a capability
- Are unrelated

Artifact state and relationship type are stored separately. For example, a closed issue is not automatically considered an implemented solution.

## Local deployment

The local prototype uses Docker Compose with independently built containers. Long-running services are started normally; batch jobs use Compose profiles.

```text
Long-running
- mariadb
- api
- ui

Batch
- importer
- github-importer (planned)
- matcher (planned)
```

Secrets and local credentials are supplied through `.env`, which is excluded from Git. `.env.example` documents required variable names using placeholders.

## AWS NGAP target mapping

| Local component | NGAP target |
|---|---|
| Streamlit container | ECS/Fargate service |
| FastAPI container | ECS/Fargate service |
| MariaDB container | Amazon RDS for MariaDB |
| Workbook and raw source files | Amazon S3 |
| Workbook importer | On-demand or scheduled ECS task |
| GitHub importer | Scheduled ECS task |
| Matching worker | Scheduled or on-demand ECS task |
| `.env` credentials | AWS Secrets Manager |
| Container output | Amazon CloudWatch Logs |
| Local browser access | NGAP-approved ingress and identity |

## Architectural boundaries

The prototype intentionally avoids unnecessary infrastructure at this stage. It does not currently require:

- Kubernetes
- Kafka
- A graph database
- A dedicated vector database
- Independently deployed microservices for every process

MariaDB, FastAPI, Streamlit, and batch containers are sufficient to validate the workflow and value proposition before introducing additional managed services.

## Security and governance principles

- Never commit credentials or tokens.
- Restrict ingestion to approved repositories and public or authorized sources.
- Preserve original evidence and source locations.
- Keep automated and human-confirmed relationships distinguishable.
- Record reviewer identity, decision, and notes for consequential changes.
- Avoid presenting a need as solved without explicit human confirmation.
