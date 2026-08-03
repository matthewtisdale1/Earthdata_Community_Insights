# Demo dataset workflow

The application can switch between the full working database and a small, curated demonstration database without changing the MariaDB volume or deleting full data.

## Databases

- Full: value of `MARIADB_DATABASE` in `.env`
- Demo: `earthdata_insights_demo` by default

`APP_DATABASE` controls which database the API reads. `DATASET_MODE` controls the visible FULL or DEMO badge in Streamlit.

## Build or refresh the demo database

From the repository root:

```powershell
.\scripts\refresh-demo.ps1 -ExampleCount 2
```

The script:

1. Drops and recreates only the demo database.
2. Copies the current full database into it.
3. Selects the highest-priority end-to-end matches, preferring Confirmed, then Uncertain, then Pending.
4. Keeps the selected needs, their evidence, organizations, report sources, artifacts, tools, repositories, and need-to-artifact matches.
5. Removes unrelated records from the demo copy.

The full database is never deleted or modified by this process.

Use one example instead:

```powershell
.\scripts\refresh-demo.ps1 -ExampleCount 1
```

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

## Safeguards

- Do not set `MARIADB_DATABASE` to the demo database. It remains the full source database.
- `APP_DATABASE` is the runtime selection.
- The demo refresh script recreates only `earthdata_insights_demo` unless a different `-DemoDatabase` is explicitly supplied.
- Review actions performed while in demo mode affect only the demo database.
