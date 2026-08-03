# ADR 0001: Use MariaDB as the initial system of record

- Status: Accepted
- Date: 2026-08-03

## Context

The prototype needs a relational system of record for canonical needs, supporting evidence, organizations, sources, review activity, and future many-to-many links to implementation artifacts.

The initial deployment target is a local Docker demonstration, with a future path to AWS NGAP.

## Decision

Use MariaDB for the initial prototype and planned NGAP pilot.

## Rationale

- The project data is strongly relational.
- Foreign keys and transactions support traceability and review workflows.
- Full-text indexing is available for evidence and artifact search.
- MariaDB runs cleanly in Docker for local demonstrations.
- Amazon RDS for MariaDB provides a straightforward managed deployment path.
- The team identified MariaDB as the preferred initial database.

## Consequences

Positive:

- One database can support the prototype without additional infrastructure.
- Local and NGAP environments can use similar database behavior.
- SQL views can expose summary metrics such as recurring-signal counts.

Tradeoffs:

- Native graph traversal is limited compared with a graph database.
- Native vector features depend on MariaDB version and may not be available in the current local image.
- Some advanced search workloads may eventually be better served by OpenSearch or another specialized index.

## Revisit when

Reevaluate this decision if artifact volume, semantic search, graph traversal, or operational constraints cannot be met without excessive complexity. MariaDB should remain the authoritative relational store even if a secondary search index is introduced.
