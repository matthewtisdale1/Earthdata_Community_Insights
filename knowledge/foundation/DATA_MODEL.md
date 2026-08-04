# ECI Data Model

ECI separates immutable source evidence from curated knowledge and reviewer-approved assessments.

## Core Entities

### Evidence

An immutable assertion extracted from a source. Evidence preserves original wording, source, year, section or page, and originating organization as it existed at the time.

### Canonical Need

A concise, enduring, Earthdata-wide user outcome. A canonical need is solution-independent, evidence-backed, and written so it can be mapped to capabilities and assessed for coverage.

### Capability

An implementation-independent ability Earthdata can provide to address one or more needs, such as data discovery, subsetting, visualization, programmatic access, documentation, or cloud processing.

### Gap Assessment

A versioned, human-reviewed judgment describing how well a need is addressed. Coverage may be unassessed, unmet, minimal, partial, mostly complete, or addressed. Scores never replace the reviewer rationale.

### Initiative

Planned, active, or completed work intended to improve one or more capabilities or reduce one or more gaps.

### Investment Priority

A decision-support view derived from community impact, gap severity, strategic alignment, initiatives, and reviewer judgment. It is explainable output rather than an independently imported fact.

## Relationships

```text
Evidence ──supports──> Canonical Need
Canonical Need ──requires──> Capability
Canonical Need ──has──> Gap Assessment
Initiative ──addresses──> Canonical Need
Initiative ──delivers──> Capability
Impact + Gap + Judgment ──inform──> Investment Priority
```

Evidence and canonical needs have a many-to-many relationship. One evidence assertion may support multiple outcomes, and one canonical need may be supported by evidence from many years, communities, organizations, and future Science Spheres.

## Reference Data

Themes, communities, source types, missions, tools, organizations, and Science Spheres classify or contextualize the core entities. They are controlled vocabularies or reference records rather than owners of canonical needs.

## Design Rules

1. Original evidence text is never overwritten.
2. Canonical needs are not assigned to a DAAC, organization, mission, tool, or Science Sphere.
3. Historical organization provenance is retained even when future mappings change.
4. Evidence counts are signals of support, not estimates of represented users.
5. Impact and opportunity scores expose their components and method version.
6. Reviewer-adjusted scores remain separate from calculated scores.
7. Gap and investment claims require review status, rationale, reviewer, and date.
8. Existing records are migrated additively until replacement workflows are validated.

## Canonical Need Quality Standard

A publishable canonical need is:

- user-centered;
- Earthdata-wide;
- solution-independent;
- supported by linked evidence;
- limited to one primary outcome; and
- actionable through one or more capability mappings.