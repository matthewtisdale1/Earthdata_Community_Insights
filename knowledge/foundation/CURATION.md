# Knowledge Curation

## Workflow

```text
Source material
    ↓
Immutable evidence
    ↓
Human review
    ↓
Canonical need and capability mapping
    ↓
Gap assessment
    ↓
Published knowledge and investment analysis
```

AI suggestions may assist at review steps but do not publish or approve knowledge.

## Review Decisions

- **Approve** — confirm the proposed mapping or wording.
- **Edit** — improve curated wording without changing original evidence.
- **Merge** — link evidence to an existing canonical need or consolidate duplicates.
- **Split** — represent multiple independent outcomes separately.
- **Retire** — supersede a canonical need while preserving history.
- **Research** — defer publication until additional context is available.

## Reviewer Checklist

Before publishing a canonical need, confirm that it:

1. describes what Earthdata users need, not what a named product should build;
2. expresses one primary outcome;
3. is understandable without the source document;
4. is supported by at least one linked evidence record;
5. preserves source provenance and historical organization context;
6. maps to one or more implementation-independent capabilities; and
7. includes a review decision, rationale, reviewer, and timestamp.

## Evidence Rules

- Preserve original wording exactly as captured.
- Store section, page, year, source, and originating organization when available.
- Mark duplicates rather than deleting them when they are useful for provenance.
- Do not infer the number of users represented by an evidence statement.
- Record extraction or matching confidence separately from human review status.

## Assessment Rules

Gap and impact assessments are versioned. Calculated values and reviewer-adjusted values are stored separately. A published assessment must explain coverage, gap severity, and any strategic-alignment judgment.

## Definition of Done

A curation decision is complete when supporting evidence is linked, canonical wording is approved, capability mappings are reviewed, rationale and reviewer identity are recorded, and the resulting record remains traceable to its source.