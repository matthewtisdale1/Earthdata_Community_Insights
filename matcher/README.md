# Need-to-artifact matcher

This batch worker creates candidate links between canonical community needs and imported implementation artifacts.

The matcher combines deterministic weighted token overlap with capability-aware phrase scoring. It does not declare that an artifact solves a need. Every new candidate begins with `review_status = Pending` and must be reviewed in the Streamlit **Implementation Matches** page or the Need Detail **Implementation** tab.

## Focused NEED-0042 Harmony test

```powershell
$env:TOOL_CODE = "HARMONY"
$env:NEED_CODE = "NEED-0042"
$env:MIN_MATCH_SCORE = "0.22"
$env:MAX_MATCHES_PER_NEED = "10"

docker compose -f .\docker_compose.yaml `
  --profile match `
  run --rm --no-deps matcher

Remove-Item Env:TOOL_CODE
Remove-Item Env:NEED_CODE
Remove-Item Env:MIN_MATCH_SCORE
Remove-Item Env:MAX_MATCHES_PER_NEED
```

This run gives additional weight to explicit subsetting language such as:

- spatial subsetting
- variable subsetter
- temporal subsetting
- bounding box
- shapefile subsetting
- `capabilities.subsetting`
- HOSS

Pending machine-generated matches for the selected need and tool are replaced before the new candidates are written. Confirmed, rejected, or uncertain human reviews are preserved.

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
$env:REPLACE_PENDING = "false"
```

Higher minimum scores reduce the review queue. `REPLACE_PENDING` defaults to `true`; set it to `false` to retain older pending machine candidates. The defaults are intended for prototype evaluation rather than production-quality classification.

## Review classifications

- Tracks Need
- Proposes Solution
- Partially Addresses
- Fully Addresses
- Implements
- Documents
- Unrelated

A closed issue or pull request is not considered implemented unless a reviewer explicitly confirms an appropriate relationship.
