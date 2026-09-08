# PI planning and ASSET transition prototype

This extension retains ECI's Streamlit / FastAPI / MariaDB stack and existing need IDs. It adds delivery commitments and outcome assessments without overwriting historical report dispositions or curation status.

## Run on Windows

From the existing repository checkout, check out `feature/pi-planning-asset-tracking` and run:

```powershell
.\scripts\enable-planning.ps1
```

The script builds the API/UI, starts MariaDB, applies an additive, repeatable migration, and starts the application. It does not delete volumes or import/replace evidence. Existing databases retain their data. The selected database comes from Docker Compose's `DATABASE_URL`; use the desired dataset configuration before running the script. A new installation still needs the existing ECI import/migration setup for its other features.

Open http://127.0.0.1:8501/planning. Add a team and PI, then create a deliverable using an existing need code from the Needs page. Record acceptance criteria, owner, PI, and external delivery references. Create multiple deliverables for a need that spans multiple teams or PIs.

## Behavior

- Scheduled deliverables require both a team and PI. Backlog items can be unassigned.
- Delivered work requires completion evidence and reviewer attribution.
- Edits require a reason. History records prior/new values, reviewer and timestamp.
- Stale edits return a conflict rather than overwrite newer changes.
- Reassignment records the prior team and new team in history. Original DAAC attribution remains attached to community evidence.
- Outcome assessments are append-only and separate from delivery status. Latest assessments and full history are visible.
- Closing an issue or delivering a task does not automatically mark a need satisfied.
- No ASSET names or DAAC-to-ASSET mappings are assumed.

## Findings from initial report review

The four reports were text-extracted and recommendation/disposition sections sampled; this is not a complete reconciled needs inventory.

- 2021 ASDC sections 3.4–3.7 describe feedback continuity problems and follow-up recommendations. Store source references and track response decisions.
- 2022 NSIDC content requests cloud cost-estimation guidance. Similar guidance appears in the 2024 Summit recommendations. Recurrence should support an existing need when intent matches, rather than silently duplicate it.
- 2023 GHRC section 5.3.1 explicitly modifies, merges, closes and renumbers prior recommendations. Preserve evidence-level dispositions separately from canonical needs and current planning state.
- 2024 Summit recommendations contain 2025 updates. Preserve report year and update dates separately. They distinguish green follow-up text and struck-through completed tasks; plain text alone loses completion evidence.
- The 2024 Metadata Compliance Checker recommendation includes publication and outreach: publication is reported complete while publicity remains to do. Model separate deliverables with separate acceptance criteria.
- Summit endorsement counts are qualified by when items were added, and dissenting views are retained. Counts should not automatically set program priority.

## Next increments

1. Reconcile existing imported evidence against these document revisions, preserving tables, runs, strikethrough, source locations, and update dates in staging.
2. Curate recurring, split and superseded needs with explicit human decisions.
3. Add an effective-dated organizational transition registry once ASSET mappings are supplied; current implementation supports deliverable-level reassignment history only.
4. Add PI capacity, dependencies, objectives, and carryover snapshots as planning practice is defined.
5. Add optional model-assisted extraction only after choosing an accessible endpoint. Existing ChatGSFC handoff remains supported conceptually; this change adds no API dependency or automated model calls.

## Validation and limits

API integration tests use SQLite to verify ownership changes, stale-write rejection, completion requirements and independent append-only outcome reviews. MariaDB SQL and Windows Docker Desktop execution require validation on the target environment; Docker is unavailable in the development workspace.

Reviewer names are self-entered. This local prototype has no authenticated role enforcement and should not be exposed as a shared production service. Existing API curation fields remain distinct from the new reviewed outcome records.
