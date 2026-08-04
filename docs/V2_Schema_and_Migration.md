# ECI v2 Schema and Migration Approach

## Purpose

ECI v2 extends the current prototype into a decision-support system that identifies high-impact unmet Earthdata user needs and connects them to capabilities and development initiatives.

The migration is intentionally additive. The existing application continues to use the current tables and views while v2 relationships and assessments are validated.

## Design principles

1. **Evidence retains provenance.** Source, year, originating organization, section, page, and original wording remain attached to evidence.
2. **Canonical needs are Earthdata-wide.** A need is not owned by a DAAC, organization, or Science Sphere.
3. **Evidence and needs are many-to-many.** One evidence statement can support multiple needs, and one need can be supported by evidence from many sources.
4. **Organizations are historical context.** Science Sphere mappings are separate, dated, reviewer-controlled reference data.
5. **Evidence counts are not user counts.** Breadth and impact must not be inferred solely from the number of records.
6. **Gap claims require review.** Coverage, gap severity, and investment opportunity scores remain draft until approved by a human reviewer.
7. **Scores remain explainable.** Component scores and reviewer overrides are retained alongside the final result.

## v2 objects

| Object | Purpose |
|---|---|
| `evidence_need_links` | Many-to-many, reviewed mappings between evidence and canonical needs |
| `science_spheres` | Current and future Science Sphere reference records |
| `organization_sphere_mappings` | Dated mappings from historical organizations to Science Spheres |
| `need_assessments` | Versioned impact, coverage, gap, and opportunity assessments |
| `initiatives` | Proposed, active, completed, or retired development investments |
| `initiative_needs` | Reviewed claims that an initiative addresses a need |
| `initiative_capabilities` | Reviewed claims that an initiative delivers a capability |

The migration also adds source section, source page, captured organization name, and immutability timestamp fields to `evidence`.

## Compatibility strategy

The first migration does **not**:

- remove `evidence.need_id`;
- replace `v_need_summary`;
- change existing API endpoints;
- change importer behavior;
- automatically approve assessments or mappings.

Current `evidence.need_id` relationships are copied into `evidence_need_links`. During the compatibility period, the legacy field remains the source used by the current API.

New v2 development should read `evidence_need_links`. After the application and importer have been migrated and validated, a later migration can make `evidence.need_id` nullable-only legacy data or remove it.

## Impact and opportunity assessment

`need_assessments` stores five explainable impact components, each on a 0–100 scale:

| Component | Meaning |
|---|---|
| Evidence strength | Quality and independence of the supporting evidence |
| Source breadth | Breadth of distinct reports and engagement sources |
| Persistence | Repeated support over time |
| Community breadth | Diversity of user communities represented |
| Strategic alignment | Alignment with approved Earthdata priorities |

Gap severity is separately assessed on a 0–100 scale:

- `0`: fully addressed;
- `25`: largely addressed;
- `50`: partially addressed;
- `75`: minimally addressed;
- `100`: unmet.

A future scoring service may calculate:

```text
impact = weighted average of approved impact components
opportunity = impact × gap severity / 100
```

The database stores both calculated values and reviewer-adjusted values. Dashboards should use the reviewer value when present.

## Migration sequence

### Phase 1: Additive schema

Run `database/migrations/010_v2_investment_model.sql` against a copy of the current database.

Expected effects:

- existing application tables remain intact;
- existing evidence-to-need links are backfilled;
- new tables and v2 views are available;
- no assessment is automatically approved.

### Phase 2: Validation dataset

Import the curated ASDC evidence as the first validation dataset. Verify:

- original wording and source provenance are preserved;
- an evidence record can support multiple canonical needs;
- the same need can be supported by multiple organizations and years;
- organization-to-Sphere mappings do not change canonical need ownership.

### Phase 3: Application adoption

Add v2 API endpoints and reviewer interfaces for:

1. evidence-to-need mapping;
2. gap assessment;
3. initiative mapping;
4. investment opportunities.

Existing UI pages remain available until v2 views have been validated.

### Phase 4: Legacy retirement

Only after the importer, API, UI, and validation checks use `evidence_need_links` should a separate migration retire direct reliance on `evidence.need_id`.

## Validation queries

```sql
-- Every legacy evidence-to-need assignment should have a v2 link.
SELECT COUNT(*) AS missing_links
FROM evidence e
LEFT JOIN evidence_need_links enl
  ON enl.evidence_id = e.evidence_id
 AND enl.need_id = e.need_id
WHERE e.need_id IS NOT NULL
  AND enl.evidence_need_link_id IS NULL;

-- Canonical needs must remain independent of organization ownership.
SELECT need_code, canonical_need
FROM needs
WHERE canonical_need IS NULL OR TRIM(canonical_need) = '';

-- No opportunity should be treated as approved without human approval.
SELECT need_id, assessment_version
FROM need_assessments
WHERE assessment_status = 'Approved'
  AND (approved_by IS NULL OR approved_at IS NULL);

-- Review the highest draft opportunities; do not interpret them as final.
SELECT *
FROM v_investment_opportunities
WHERE assessment_status = 'Draft'
ORDER BY opportunity_score DESC;
```

## Rollback approach

Because this migration is additive, application rollback is accomplished by returning to the existing application code. The new tables can remain unused without affecting current behavior.

Dropping v2 objects should be performed only through a dedicated rollback script after confirming no v2 data must be retained. The migration does not automatically drop or overwrite legacy data.
