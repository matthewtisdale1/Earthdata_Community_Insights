import json
import os
import re
from collections import Counter

from sqlalchemy import create_engine, text

DATABASE_URL = os.environ["DATABASE_URL"]
MIN_SCORE = float(os.environ.get("MIN_MATCH_SCORE", "0.22"))
MAX_PER_NEED = int(os.environ.get("MAX_MATCHES_PER_NEED", "15"))
TOOL_CODE = os.environ.get("TOOL_CODE", "").strip()
NEED_CODE = os.environ.get("NEED_CODE", "").strip()
REPLACE_PENDING = os.environ.get("REPLACE_PENDING", "true").lower() == "true"

STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "into", "their",
    "they", "them", "users", "user", "need", "needs", "data", "support",
    "provide", "allow", "using", "use", "more", "across", "within", "about",
    "have", "has", "are", "was", "were", "will", "would", "could", "should",
}

# Capability concepts supplement token overlap with domain-specific phrases. A concept
# is activated only when the need text contains one of its phrases. Artifacts then
# receive stronger credit for explicit capability language than for generic words.
CAPABILITY_CONCEPTS = {
    "subsetting": {
        "need_phrases": [
            "subset", "subsetting", "spatial subset", "spatial subsetting",
            "variable subset", "variable subsetting", "temporal subset",
            "temporal subsetting", "bounding box", "shapefile subset",
        ],
        "artifact_phrases": {
            "subsetting": 0.18,
            "subset": 0.12,
            "spatial subsetting": 0.28,
            "spatial subset": 0.25,
            "variable subsetter": 0.28,
            "variable subsetting": 0.25,
            "temporal subsetting": 0.25,
            "bounding box": 0.22,
            "shapefile subsetting": 0.25,
            "shape file subsetting": 0.25,
            "capabilities.subsetting": 0.32,
            "hoss": 0.15,
            "subsetter": 0.16,
        },
    },
}

engine = create_engine(DATABASE_URL, pool_pre_ping=True)


def normalize(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value.lower()).strip()


def tokens(value: str | None) -> list[str]:
    if not value:
        return []
    return [
        token for token in re.findall(r"[a-z0-9][a-z0-9_-]{2,}", value.lower())
        if token not in STOPWORDS
    ]


def need_text(row: dict) -> str:
    return normalize(" ".join([
        row.get("canonical_need") or "",
        row.get("need_summary") or "",
        row.get("desired_outcome") or "",
        row.get("need_category") or "",
    ]))


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


def active_concepts(row: dict) -> list[str]:
    text_value = need_text(row)
    return [
        concept_name
        for concept_name, concept in CAPABILITY_CONCEPTS.items()
        if any(phrase in text_value for phrase in concept["need_phrases"])
    ]


def score(
    terms: Counter,
    concepts: list[str],
    artifact: dict,
) -> tuple[float, list[str], list[str]]:
    title_text = normalize(artifact.get("title"))
    body_text = normalize(artifact.get("body"))
    labels_text = normalize(" ".join(json.loads(artifact.get("labels_json") or "[]")))
    combined_text = " ".join([title_text, body_text, labels_text])

    title = Counter(tokens(title_text))
    body = Counter(tokens(body_text))
    labels = Counter(tokens(labels_text))
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

    phrase_bonus = 0.0
    matched_phrases: list[str] = []
    for concept_name in concepts:
        concept = CAPABILITY_CONCEPTS[concept_name]
        for phrase, weight in concept["artifact_phrases"].items():
            if phrase in combined_text:
                # Explicit wording in a title is more persuasive than a body mention.
                multiplier = 1.25 if phrase in title_text else 1.0
                phrase_bonus += weight * multiplier
                matched_phrases.append(phrase)

    # Cap phrase contribution so lexical evidence still matters while allowing an
    # explicit domain phrase to outrank generic token overlap.
    phrase_score = min(0.55, phrase_bonus)

    metadata = 0.0
    if artifact.get("artifact_type") == "release":
        metadata += 0.03
    if artifact.get("state") == "closed":
        metadata += 0.02

    overall = min(1.0, lexical * 0.65 + phrase_score + metadata)
    return overall, sorted(set(matched_terms)), sorted(set(matched_phrases))


def main() -> None:
    with engine.begin() as connection:
        need_sql = """
            SELECT need_id, need_code, canonical_need, need_summary,
                   desired_outcome, need_category
            FROM needs
            WHERE COALESCE(lifecycle_status, '') NOT IN ('Rejected', 'Duplicate')
        """
        need_params = {}
        if NEED_CODE:
            need_sql += " AND need_code = :need_code"
            need_params["need_code"] = NEED_CODE

        needs = [
            dict(row)
            for row in connection.execute(text(need_sql), need_params).mappings()
        ]

        artifact_sql = """
            SELECT ia.artifact_id, ia.artifact_type, ia.title, ia.body,
                   ia.state, ia.labels_json, t.tool_code
            FROM implementation_artifacts ia
            JOIN tools t ON t.tool_id = ia.tool_id
        """
        artifact_params = {}
        if TOOL_CODE:
            artifact_sql += " WHERE t.tool_code = :tool_code"
            artifact_params["tool_code"] = TOOL_CODE
        artifacts = [
            dict(row)
            for row in connection.execute(text(artifact_sql), artifact_params).mappings()
        ]

        if REPLACE_PENDING and needs:
            delete_sql = """
                DELETE nam
                FROM need_artifact_matches nam
                JOIN needs n ON n.need_id = nam.need_id
                JOIN implementation_artifacts ia ON ia.artifact_id = nam.artifact_id
                JOIN tools t ON t.tool_id = ia.tool_id
                WHERE nam.review_status = 'Pending'
                  AND nam.match_method IN ('weighted-token-overlap', 'capability-aware-lexical')
            """
            delete_params = {}
            if NEED_CODE:
                delete_sql += " AND n.need_code = :need_code"
                delete_params["need_code"] = NEED_CODE
            if TOOL_CODE:
                delete_sql += " AND t.tool_code = :tool_code"
                delete_params["tool_code"] = TOOL_CODE
            connection.execute(text(delete_sql), delete_params)

        updated = 0
        for need in needs:
            terms = need_terms(need)
            concepts = active_concepts(need)
            candidates = []
            for artifact in artifacts:
                overall, matched_terms, matched_phrases = score(
                    terms, concepts, artifact
                )
                if overall >= MIN_SCORE and (matched_terms or matched_phrases):
                    candidates.append(
                        (overall, matched_terms, matched_phrases, artifact)
                    )
            candidates.sort(key=lambda item: item[0], reverse=True)

            for overall, matched_terms, matched_phrases, artifact in candidates[:MAX_PER_NEED]:
                evidence_parts = []
                if matched_phrases:
                    evidence_parts.append(
                        "Capability phrases: " + ", ".join(matched_phrases[:20])
                    )
                if matched_terms:
                    evidence_parts.append(
                        "Matched terms: " + ", ".join(matched_terms[:20])
                    )

                connection.execute(text("""
                    INSERT INTO need_artifact_matches (
                        need_id, artifact_id, relationship_type,
                        lexical_score, overall_score, matched_terms,
                        match_explanation, match_method, matcher_version,
                        review_status
                    ) VALUES (
                        :need_id, :artifact_id, 'Potential Match',
                        :score, :score, :matched_terms,
                        :explanation, 'capability-aware-lexical', 'prototype-1.1',
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
                    "matched_terms": json.dumps({
                        "terms": matched_terms,
                        "phrases": matched_phrases,
                        "concepts": concepts,
                    }),
                    "explanation": "; ".join(evidence_parts),
                })
                updated += 1

    print(
        f"Matching complete: {len(needs)} needs, {len(artifacts)} artifacts, "
        f"{updated} candidate links created or updated."
    )


if __name__ == "__main__":
    main()
