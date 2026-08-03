# Project Documentation

This directory contains design and planning documentation for Earthdata Community Insights.

## Core documents

- [Architecture](architecture.md) — current components, planned ingestion and matching services, local deployment, and NGAP mapping
- [Data model](data-model.md) — current relational model, planned implementation-intelligence entities, diagrams, and data-quality rules
- [Roadmap](roadmap.md) — phased development plan from the workbook prototype through an NGAP pilot

## Architecture decision records

Architecture decision records document important technical and governance choices and the reasons behind them.

- [ADR 0001: Use MariaDB](decisions/0001-use-mariadb.md)
- [ADR 0002: Use FastAPI](decisions/0002-use-fastapi.md)
- [ADR 0003: Use Streamlit](decisions/0003-use-streamlit.md)
- [ADR 0004: Require human review](decisions/0004-require-human-review.md)

## Documentation principles

- Describe current behavior separately from planned behavior.
- Keep source traceability and human-review requirements explicit.
- Update architecture and data-model documentation alongside significant code or schema changes.
- Record consequential technology or governance decisions as ADRs.
