# ADR 0003: Use Streamlit for the prototype user interface

- Status: Accepted
- Date: 2026-08-03

## Context

The project needs a usable demonstration interface for exploring needs, evidence, organizations, sources, and review workflows. The initial priority is rapid iteration with a small Python codebase rather than building a full production web frontend.

## Decision

Use Streamlit for the prototype user interface.

## Rationale

- It enables rapid development of data-oriented pages and filters.
- It integrates well with Python, pandas, and the FastAPI service.
- Multipage navigation supports list, detail, dashboard, and review screens.
- The UI can be packaged as an independent container.
- It is appropriate for demonstrating the workflow before final production-interface requirements are known.

## Consequences

Positive:

- Features can be demonstrated quickly.
- Data tables, charts, metrics, and review controls require relatively little code.
- The local developer workflow remains Python-centered.

Tradeoffs:

- Fine-grained frontend behavior and styling are more constrained than with a dedicated JavaScript framework.
- Session-state navigation must be managed carefully.
- Production accessibility, identity integration, and large-scale concurrency require evaluation.

## Revisit when

Consider a dedicated frontend framework if user research identifies requirements that Streamlit cannot meet, or if production concurrency, accessibility, identity integration, or interaction complexity becomes a limiting factor. The FastAPI boundary should allow the UI to be replaced without redesigning the data model.
