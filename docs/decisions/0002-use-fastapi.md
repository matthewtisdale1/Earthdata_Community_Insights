# ADR 0002: Use FastAPI for the application API

- Status: Accepted
- Date: 2026-08-03

## Context

The Streamlit interface needs a stable service boundary for querying and updating community-needs data. Future clients, batch workflows, and NGAP deployment should not depend on UI-specific database access.

## Decision

Use FastAPI as the REST API layer between the user interface and MariaDB.

## Rationale

- It provides typed request and response validation through Python models.
- Interactive OpenAPI documentation supports development and demonstrations.
- It fits the existing Python-based importer and UI ecosystem.
- It is lightweight enough for the prototype and suitable for container deployment.
- It provides a clear place for shared business rules and authorization checks.

## Consequences

Positive:

- UI code does not need direct database credentials.
- API endpoints can be tested independently.
- Future clients can reuse the same service.
- The service maps naturally to ECS/Fargate.

Tradeoffs:

- API schemas and database migrations must be kept synchronized.
- Long-running ingestion and matching work should not run inside normal web requests.
- Authentication and authorization still need to be designed for NGAP.

## Guidance

- Keep database access and shared business rules in the API or dedicated service modules.
- Use separate batch containers for workbook import, GitHub synchronization, and matching.
- Return traceable identifiers and source URLs in API responses.
- Add automated endpoint tests as the API expands.
