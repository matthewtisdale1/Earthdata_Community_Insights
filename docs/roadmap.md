# Roadmap

This roadmap organizes development around demonstrable user value. Dates are intentionally omitted until priorities, contributors, and deployment constraints are confirmed.

## Version 0.1 — Workbook prototype

**Goal:** Establish a traceable system for recurring community needs.

Status: substantially implemented.

- Import structured UWG information from Excel
- Store canonical needs and original evidence
- Browse and filter needs
- Browse evidence, sources, and organizations
- Review and edit canonical needs
- Calculate prototype signal scores
- Run locally with Docker Compose

Exit criteria:

- A new developer can clone and run the prototype using documented steps.
- Original evidence remains traceable to a source and location.
- Human review changes are stored without overwriting source evidence.

## Version 0.2 — Earthdata tool catalog

**Goal:** Establish the tools and repositories that may address community needs.

Initial scope:

- Earthdata Search
- Worldview
- GIBS
- CMR
- Harmony

Planned work:

- Add `tools` and `external_sources` tables
- Seed the initial five tools
- Register approved GitHub repositories
- Add tool summary and detail API endpoints
- Add Tools and Tool Details UI pages
- Display repository sync status

Exit criteria:

- Each initial tool has an owner, description, homepage, and approved source list.
- Users can navigate from a tool to its repositories and artifacts.

## Version 0.3 — GitHub artifact ingestion

**Goal:** Import implementation activity in a repeatable, traceable way.

Planned work:

- Add `implementation_artifacts` and `artifact_relationships`
- Create a profile-based GitHub importer container
- Import issues, pull requests, and releases
- Preserve external IDs, URLs, labels, milestones, state, and timestamps
- Support incremental synchronization
- Record sync errors and last successful run
- Add artifact list and detail API endpoints
- Add Implementation Artifacts UI page

Exit criteria:

- The importer can be rerun without creating duplicate artifacts.
- Each artifact retains its source repository and external URL.
- Failed repository syncs do not prevent successful sources from being retained.

## Version 0.4 — Need-to-artifact matching

**Goal:** Identify candidate implementation activity relevant to community needs.

Planned work:

- Add `need_artifact_matches`
- Implement lexical and metadata-based candidate generation
- Store matcher method, version, scores, and explanation
- Limit candidate volume per need
- Add a human Match Review queue
- Add Implementations tab to Need Details
- Support confirm, partial, full, documents, tracks, and reject decisions
- Report needs with no confirmed implementation

Exit criteria:

- Reviewers can understand why a candidate was proposed.
- Automated candidates are visibly different from confirmed relationships.
- A closed issue is never automatically reported as a solved need.

## Version 0.5 — Quality evaluation and semantic matching

**Goal:** Improve match quality using reviewed examples.

Planned work:

- Build a labeled evaluation set from human decisions
- Measure precision at the top candidate ranks
- Identify common false-positive patterns
- Add synonyms and capability vocabulary
- Evaluate embedding-based reranking
- Compare MariaDB, Python, and managed search options
- Version and monitor matcher behavior

Exit criteria:

- Semantic matching is added only if it measurably improves reviewed outcomes.
- Matcher changes can be compared against a stable evaluation set.

## Version 0.6 — Documentation and capability coverage

**Goal:** Look beyond tickets to identify capabilities that already exist.

Planned work:

- Add controlled documentation ingestion
- Add release-note and changelog ingestion
- Introduce a capability catalog
- Connect needs to capabilities and capabilities to tools
- Capture issue → pull request → release → documentation chains
- Add cross-tool capability views

Exit criteria:

- Users can distinguish a planned ticket from an available, documented capability.
- The system can show multiple tools that satisfy the same capability.

## Version 0.7 — NGAP pilot

**Goal:** Deploy an operational pilot in AWS NGAP.

Planned work:

- Package UI and API for ECS/Fargate
- Migrate MariaDB to Amazon RDS
- Store source documents and raw API responses in S3
- Store credentials in Secrets Manager
- Send logs and metrics to CloudWatch
- Schedule importer and matcher ECS tasks
- Implement NGAP-approved ingress and identity
- Add backup, recovery, and operational procedures

Exit criteria:

- No long-lived credentials are stored in images or source control.
- Services can be deployed and rolled back through a repeatable process.
- Scheduled synchronization and matching are observable and recoverable.

## Cross-cutting work

The following should develop incrementally across all versions:

- Automated tests
- Database migration discipline
- API validation and error handling
- Accessibility and UI usability
- Auditability of review decisions
- Security review
- Data-governance documentation
- Contributor guidance
- Architecture decision records

## Items intentionally deferred

These are not required to prove the initial value proposition:

- Kubernetes
- Kafka or another event-streaming platform
- A dedicated graph database
- A dedicated vector database
- Fully autonomous implementation classification
- Broad web crawling without an approved source registry
