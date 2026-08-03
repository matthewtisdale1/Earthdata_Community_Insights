# Need-to-artifact matcher

This batch worker creates candidate links between canonical community needs and imported implementation artifacts.

The first prototype matcher uses deterministic weighted token overlap. It does not declare that an artifact solves a need. Every candidate begins with `review_status = Pending` and must be reviewed in the Streamlit **Implementation Matches** page.

## Run Harmony only

```powershell
$env:TOOL_CODE = "HARMONY"
docker compose -f .\docker_compose.yaml --profile match run --rm --no-deps matcher
Remove-Item Env:TOOL_CODE
```

## Run all imported tools

```powershell
docker compose -f .\docker_compose.yaml --profile match run --rm --no-deps matcher
```

## Optional tuning

```powershell
$env:MIN_MATCH_SCORE = "0.30"
$env:MAX_MATCHES_PER_NEED = "10"
```

Higher minimum scores reduce the review queue. The defaults are intended for prototype evaluation rather than production-quality classification.

## Review classifications

- Tracks Need
- Proposes Solution
- Partially Addresses
- Fully Addresses
- Implements
- Documents
- Unrelated

A closed issue is not considered implemented unless a reviewer explicitly confirms an appropriate relationship.
