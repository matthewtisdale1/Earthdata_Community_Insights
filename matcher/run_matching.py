import json
import os
import re
from collections import Counter

from sqlalchemy import create_engine, text

DATABASE_URL = os.environ["DATABASE_URL"]
MIN_SCORE = float(os.environ.get("MIN_MATCH_SCORE", "0.22"))
MAX_PER_NEED = int(os.environ.get("MAX_MATCHES_PER_NEED", "15"))
TOOL_CODE = os.environ.get("TOOL_CODE", "").strip()

STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "into", "their",
    "they", "them", "users", "user", "need", "needs", "data", "support",
    "provide", "allow", "using", "use", "more", "across", "within", "about",
    "have", "has", "are", "was", "were", "will", "would", "could", "should",
}

engine = create_engine(DATABASE_URL, pool_pre_ping=True)


def tokens(value: str | None) -> list[str]:
    if not value:
        return []
    return [
        token for token in re.findall(r"[a-z0-9][a-z0-9_-]{2,}", value.lower())
        if token not in STOPWORDS
    ]


def need_terms(row: dict) -> Counter:
    weighted = Counter()
    for token in tokens(row.get("canonical_need")):
        weighted[token] += 4
    for token in tokens(row.get("need_summary")):
        weighted[token] += 2
    for token in tokens(row.get("desired_outcome")):
        weighted[token] += 2
    for token in tokens(row.get("need_category")):
        weighted[token] += 1
    return weighted


def score(terms: Counter, artifact: dict) -> tuple[float, list[str]]:
    title = Counter(tokens(artifact.get("title")))
    body = Counter(tokens(artifact.get("body")))
    labels = Counter(tokens(" ".join(json.loads(artifact.get("labels_json") or "[]"))))
    denominator = sum(terms.values()) or 1
    matched = 0.0
    matched_terms: list[str] = []

    for term, weight in terms.items():
        contribution = 0.0
        if title[term]:
            contribution = max(contribution, weight)
        if labels[term]:
            contribution = max(contribution, weight * 0.9)
        if body[term]:
            contribution = max(contribution, weight * 0.45)
        if contribution:
            matched += contribution
            matched_terms.append(term)

    lexical = min(1.0, matched / denominator)
    metadata = 0.0
    if artifact.get("artifact_type") == "release":
        metadata += 0.03
    if artifact.get("state") == "closed":
        metadata += 0.02
    return min(1.0, lexical * 0.95 + metadata), sorted(set(matched_terms))


def main() -> None:
    with engine.begin() as connection:
        needs = [dict(row) for row in connection.execute(text("""
            SELECT need_id, need_code, canonical_need, need_summary,
                   desired_outcome, need_category
            FROM needs
            WHERE COALESCE(lifecycle_status, '') NOT IN ('Rejected', 'Duplicate')
        """)).mappings()]

        artifact_sql = """
            SELECT ia.artifact_id, ia.artifact_type, ia.title, ia.body,
                   ia.state, ia.labels_json, t.tool_code
            FROM implementation_artifacts ia
            JOIN tools t ON t.tool_id = ia.tool_id
        """
        params = {}
        if TOOL_CODE:
            artifact_sql += " WHERE t.tool_code = :tool_code"
            params["tool_code"] = TOOL_CODE
        artifacts = [dict(row) for row in connection.execute(text(artifact_sql), params).mappings()]

        updated = 0
        for need in needs:
            terms = need_terms(need)
            candidates = []
            for artifact in artifacts:
                overall, matched_terms = score(terms, artifact)
                if overall >= MIN_SCORE and matched_terms:
                    candidates.append((overall, matched_terms, artifact))
            candidates.sort(key=lambda item: item[0], reverse=True)

            for overall, matched_terms, artifact in candidates[:MAX_PER_NEED]:
                connection.execute(text("""
                    INSERT INTO need_artifact_matches (
                        need_id, artifact_id, relationship_type,
                        lexical_score, overall_score, matched_terms,
                        match_explanation, match_method, matcher_version,
                        review_status
                    ) VALUES (
                        :need_id, :artifact_id, 'Potential Match',
                        :score, :score, :matched_terms,
                        :explanation, 'weighted-token-overlap', 'prototype-1.0',
                        'Pending'
                    )
                    ON DUPLICATE KEY UPDATE
                        lexical_score = VALUES(lexical_score),
                        overall_score = VALUES(overall_score),
                        matched_terms = VALUES(matched_terms),
                        match_explanation = VALUES(match_explanation),
                        match_method = VALUES(match_method),
                        matcher_version = VALUES(matcher_version),
                        updated_at = NOW()
                """), {
                    "need_id": need["need_id"],
                    "artifact_id": artifact["artifact_id"],
                    "score": overall,
                    "matched_terms": json.dumps(matched_terms),
                    "explanation": "Matched terms: " + ", ".join(matched_terms[:20]),
                })
                updated += 1

    print(
        f"Matching complete: {len(needs)} needs, {len(artifacts)} artifacts, "
        f"{updated} candidate links created or updated."
    )


if __name__ == "__main__":
    main()
