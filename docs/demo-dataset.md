# Demo dataset workflow

The application can switch between the full working database and a small, curated demonstration database without changing the MariaDB volume or deleting full data.

## Databases

- Full: value of `MARIADB_DATABASE` in `.env`
- Demo: `earthdata_insights_demo` by default

`APP_DATABASE` controls which database the API reads. `DATASET_MODE` controls the visible FULL or DEMO badge in Streamlit.

## Build a curated NEED-0042 demo

From the repository root:

```powershell
.\scripts\refresh-demo.ps1 -NeedCodes NEED-0042
```

This keeps `NEED-0042`, all evidence linked to it, the organizations and source reports represented by that evidence, and up to five of its highest-priority implementation matches and artifacts.

To keep more or fewer implementation artifacts:

```powershell
.\scripts\refresh-demo.ps1 `
    -NeedCodes NEED-0042 `
    -MaxArtifactsPerNeed 3
```

Multiple curated needs are also supported:

```powershell
.\scripts\refresh-demo.ps1 `
    -NeedCodes NEED-0042,NEED-0141 `
    -MaxArtifactsPerNeed 3
```

## Build an automatically selected demo

The original automatic workflow remains available:

```powershell
.\scripts\refresh-demo.ps1 -ExampleCount 2
```

When `-NeedCodes` is omitted, the script selects the highest-priority end-to-end matches, preferring Confirmed, then Uncertain, then Pending.

In either mode, the script:

1. Drops and recreates only the demo database.
2. Copies the current full database into it.
3. Selects the requested need or automatically selects matches.
4. Keeps the selected needs, their evidence, organizations, report sources, artifacts, tools, repositories, and need-to-artifact matches.
5. Removes unrelated records from the demo copy.

The full database is never deleted or modified by this process.

## Switch datasets

Demo:

```powershell
.\scripts\use-dataset.ps1 demo
```

Full:

```powershell
.\scripts\use-dataset.ps1 full
```

The switcher updates only `.env`, then recreates the API and UI containers. MariaDB remains running.

## Verify

Open:

```text
http://127.0.0.1:8501
```

The sidebar displays either `DATASET: DEMO` or `DATASET: FULL`.

API context:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/system/context
```

For a curated NEED-0042 demo, the Needs page should contain one need. Its detail page should retain the Evidence, Organizations, Implementation, and Review tabs.

## Safeguards

- Do not set `MARIADB_DATABASE` to the demo database. It remains the full source database.
- `APP_DATABASE` is the runtime selection.
- The demo refresh script recreates only `earthdata_insights_demo` unless a different `-DemoDatabase` is explicitly supplied.
- Review actions performed while in demo mode affect only the demo database.
