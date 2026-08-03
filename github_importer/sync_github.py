import hashlib
import json
import os
import sys
import time
from datetime import datetime
from typing import Any

import requests
from sqlalchemy import create_engine, text


DATABASE_URL = os.environ["DATABASE_URL"]
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
GITHUB_API_VERSION = os.environ.get("GITHUB_API_VERSION", "2022-11-28")
SOURCE_CODE = os.environ.get("SOURCE_CODE", "").strip()
FULL_SYNC = os.environ.get("FULL_SYNC", "false").lower() == "true"

engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=300)

session = requests.Session()
session.headers.update(
    {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
        "User-Agent": "earthdata-community-insights",
    }
)
if GITHUB_TOKEN:
    session.headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"


def parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)


def request_json(url: str, params: dict[str, Any] | None = None) -> tuple[Any, requests.Response]:
    response = session.get(url, params=params, timeout=60)
    if response.status_code == 403:
        raise RuntimeError(
            "GitHub request rejected. "
            f"Remaining={response.headers.get('X-RateLimit-Remaining')}, "
            f"reset={response.headers.get('X-RateLimit-Reset')}, "
            f"response={response.text[:500]}"
        )
    response.raise_for_status()
    return response.json(), response


def get_all_pages(url: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    page = 1
    records: list[dict[str, Any]] = []
    query = dict(params or {})
    query["per_page"] = 100

    while True:
        query["page"] = page
        payload, _ = request_json(url, query)
        if not isinstance(payload, list):
            raise RuntimeError(f"Expected a list response from {url}")
        records.extend(payload)
        if len(payload) < 100:
            break
        page += 1
        time.sleep(0.1)

    return records


def content_hash(title: str, body: str | None, state: str | None, updated_at: str | None) -> str:
    value = "\n".join([title or "", body or "", state or "", updated_at or ""])
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def artifact_code(owner: str, repository: str, artifact_type: str, external_id: str) -> str:
    clean_owner = owner.upper().replace("-", "_")
    clean_repo = repository.upper().replace("-", "_")
    return f"GH_{clean_owner}_{clean_repo}_{artifact_type.upper()}_{external_id}"


def upsert_artifact(connection, values: dict[str, Any]) -> None:
    connection.execute(
        text(
            """
            INSERT INTO implementation_artifacts (
                artifact_code,
                external_source_id,
                tool_id,
                artifact_type,
                external_id,
                external_number,
                title,
                body,
                state,
                state_reason,
                author_name,
                labels_json,
                milestone_name,
                external_url,
                created_external_at,
                updated_external_at,
                closed_external_at,
                merged_external_at,
                retrieved_at,
                content_hash,
                raw_metadata
            )
            VALUES (
                :artifact_code,
                :external_source_id,
                :tool_id,
                :artifact_type,
                :external_id,
                :external_number,
                :title,
                :body,
                :state,
                :state_reason,
                :author_name,
                :labels_json,
                :milestone_name,
                :external_url,
                :created_external_at,
                :updated_external_at,
                :closed_external_at,
                :merged_external_at,
                NOW(),
                :content_hash,
                :raw_metadata
            )
            ON DUPLICATE KEY UPDATE
                external_number = VALUES(external_number),
                title = VALUES(title),
                body = VALUES(body),
                state = VALUES(state),
                state_reason = VALUES(state_reason),
                author_name = VALUES(author_name),
                labels_json = VALUES(labels_json),
                milestone_name = VALUES(milestone_name),
                external_url = VALUES(external_url),
                created_external_at = VALUES(created_external_at),
                updated_external_at = VALUES(updated_external_at),
                closed_external_at = VALUES(closed_external_at),
                merged_external_at = VALUES(merged_external_at),
                retrieved_at = NOW(),
                content_hash = VALUES(content_hash),
                raw_metadata = VALUES(raw_metadata)
            """
        ),
        values,
    )


def map_issue(source: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
    artifact_type = "pull_request" if "pull_request" in item else "issue"
    labels = [label.get("name") for label in item.get("labels", []) if label.get("name")]
    milestone = item.get("milestone")

    return {
        "artifact_code": artifact_code(
            source["owner_name"], source["repository_name"], artifact_type, str(item["id"])
        ),
        "external_source_id": source["external_source_id"],
        "tool_id": source["tool_id"],
        "artifact_type": artifact_type,
        "external_id": str(item["id"]),
        "external_number": item.get("number"),
        "title": item.get("title") or "",
        "body": item.get("body"),
        "state": item.get("state"),
        "state_reason": item.get("state_reason"),
        "author_name": (item.get("user") or {}).get("login"),
        "labels_json": json.dumps(labels),
        "milestone_name": milestone.get("title") if milestone else None,
        "external_url": item.get("html_url"),
        "created_external_at": parse_date(item.get("created_at")),
        "updated_external_at": parse_date(item.get("updated_at")),
        "closed_external_at": parse_date(item.get("closed_at")),
        "merged_external_at": None,
        "content_hash": content_hash(
            item.get("title") or "", item.get("body"), item.get("state"), item.get("updated_at")
        ),
        "raw_metadata": json.dumps(item),
    }


def map_release(source: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
    title = item.get("name") or item.get("tag_name") or "Release"
    state = "draft" if item.get("draft") else "prerelease" if item.get("prerelease") else "published"

    return {
        "artifact_code": artifact_code(
            source["owner_name"], source["repository_name"], "release", str(item["id"])
        ),
        "external_source_id": source["external_source_id"],
        "tool_id": source["tool_id"],
        "artifact_type": "release",
        "external_id": str(item["id"]),
        "external_number": None,
        "title": title,
        "body": item.get("body"),
        "state": state,
        "state_reason": None,
        "author_name": (item.get("author") or {}).get("login"),
        "labels_json": json.dumps([]),
        "milestone_name": None,
        "external_url": item.get("html_url"),
        "created_external_at": parse_date(item.get("created_at")),
        "updated_external_at": parse_date(item.get("published_at")),
        "closed_external_at": None,
        "merged_external_at": None,
        "content_hash": content_hash(title, item.get("body"), state, item.get("published_at")),
        "raw_metadata": json.dumps(item),
    }


def sync_source(connection, source: dict[str, Any]) -> dict[str, int]:
    api_url = source["api_url"].rstrip("/")
    params: dict[str, Any] = {
        "state": "all",
        "sort": "updated",
        "direction": "desc",
    }

    if source.get("last_synced_at") and not FULL_SYNC:
        params["since"] = source["last_synced_at"].strftime("%Y-%m-%dT%H:%M:%SZ")

    print(f"Syncing {source['owner_name']}/{source['repository_name']}", flush=True)

    issue_records = get_all_pages(f"{api_url}/issues", params)
    issues = 0
    pull_requests = 0
    for item in issue_records:
        mapped = map_issue(source, item)
        upsert_artifact(connection, mapped)
        if mapped["artifact_type"] == "issue":
            issues += 1
        else:
            pull_requests += 1

    releases = get_all_pages(f"{api_url}/releases")
    for release in releases:
        upsert_artifact(connection, map_release(source, release))

    connection.execute(
        text(
            """
            UPDATE external_sources
            SET
                last_synced_at = NOW(),
                sync_cursor = NOW(),
                sync_status = 'Success',
                sync_error = NULL
            WHERE external_source_id = :external_source_id
            """
        ),
        {"external_source_id": source["external_source_id"]},
    )

    return {
        "issues": issues,
        "pull_requests": pull_requests,
        "releases": len(releases),
    }


def main() -> None:
    with engine.begin() as connection:
        conditions = [
            "es.active = TRUE",
            "es.sync_enabled = TRUE",
            "es.source_kind = 'github_repository'",
        ]
        params: dict[str, Any] = {}
        if SOURCE_CODE:
            conditions.append("es.source_code = :source_code")
            params["source_code"] = SOURCE_CODE

        sources = connection.execute(
            text(
                f"""
                SELECT
                    es.external_source_id,
                    es.source_code,
                    es.tool_id,
                    es.owner_name,
                    es.repository_name,
                    es.api_url,
                    es.last_synced_at
                FROM external_sources es
                WHERE {' AND '.join(conditions)}
                ORDER BY es.source_code
                """
            ),
            params,
        ).mappings().all()

        if not sources:
            raise RuntimeError("No enabled GitHub repository sources were found.")

        for source_row in sources:
            source = dict(source_row)
            try:
                counts = sync_source(connection, source)
                print(f"Completed {source['source_code']}: {counts}", flush=True)
            except Exception as error:
                connection.execute(
                    text(
                        """
                        UPDATE external_sources
                        SET sync_status = 'Failed', sync_error = :error
                        WHERE external_source_id = :external_source_id
                        """
                    ),
                    {
                        "external_source_id": source["external_source_id"],
                        "error": str(error)[:4000],
                    },
                )
                print(f"Failed {source['source_code']}: {error}", file=sys.stderr, flush=True)

    with engine.connect() as connection:
        totals = connection.execute(
            text(
                """
                SELECT artifact_type, COUNT(*) AS artifact_count
                FROM implementation_artifacts
                GROUP BY artifact_type
                ORDER BY artifact_type
                """
            )
        ).mappings().all()

    print("Artifact totals:", [dict(row) for row in totals], flush=True)


if __name__ == "__main__":
    main()
