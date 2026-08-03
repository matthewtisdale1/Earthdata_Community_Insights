import pandas as pd
import streamlit as st

import api_client as api
from navigation import goto_evidence, needs_link
from styles import breadcrumb, page_header


STATUS_OPTIONS = [
    "Candidate",
    "Validated",
    "Planned",
    "In Progress",
    "Implemented",
    "Deferred",
    "Rejected",
    "Duplicate",
]

PRIORITY_OPTIONS = [
    "Unassigned",
    "Critical",
    "High",
    "Medium",
    "Low",
]

RELATIONSHIP_OPTIONS = [
    "Potential Match",
    "Tracks Need",
    "Proposes Solution",
    "Partially Addresses",
    "Fully Addresses",
    "Implements",
    "Documents",
    "Unrelated",
]

REVIEW_STATUS_OPTIONS = [
    "Pending",
    "Confirmed",
    "Uncertain",
    "Rejected",
]


def _score_percent(value) -> str:
    if value is None:
        return "—"
    return f"{float(value) * 100:.0f}%"


def render() -> None:
    need_code = st.session_state.get("selected_need_code")

    if not need_code:
        st.warning("No need was selected.")
        needs_link(label="Return to Needs")
        return

    detail = api.get(f"/needs/{need_code}")
    need = detail["need"]
    evidence = detail["evidence"]
    artifacts = api.get(f"/needs/{need_code}/artifacts")

    organizations = sorted(
        {
            row.get("organization_name")
            for row in evidence
            if row.get("organization_name")
        }
    )

    breadcrumb("Community Needs › Need Details")
    page_header(need_code, need["canonical_need"])

    metric_columns = st.columns(6)
    metric_columns[0].metric("Signal", int(need.get("signal_score") or 0))
    metric_columns[1].metric("Evidence", need.get("evidence_count", 0))
    metric_columns[2].metric("Organizations", need.get("organization_count", 0))
    metric_columns[3].metric("Implementation", len(artifacts))
    metric_columns[4].metric("First seen", need.get("first_seen_year") or "—")
    metric_columns[5].metric("Last seen", need.get("last_seen_year") or "—")

    overview_tab, evidence_tab, organizations_tab, implementation_tab, review_tab = st.tabs(
        [
            "Overview",
            f"Evidence ({len(evidence)})",
            f"Organizations ({len(organizations)})",
            f"Implementation ({len(artifacts)})",
            "Review",
        ]
    )

    with overview_tab:
        left, right = st.columns([2, 1], gap="large")

        with left:
            st.subheader("Canonical need")
            st.write(need["canonical_need"])

            st.subheader("Desired outcome")
            if need.get("desired_outcome"):
                st.write(need["desired_outcome"])
            else:
                st.info("A desired outcome has not yet been recorded.")

            if need.get("notes"):
                st.subheader("Notes")
                st.write(need["notes"])

        with right:
            with st.container(border=True):
                st.markdown("#### Classification")
                st.write(f'**Category:** {need.get("need_category") or "Uncategorized"}')
                st.write(f'**Status:** {need.get("lifecycle_status") or "Candidate"}')
                st.write(f'**Priority:** {need.get("priority") or "Unassigned"}')
                st.write(f'**Trend:** {need.get("trend") or "Unknown"}')
                st.write(f'**Reviewed:** {"Yes" if need.get("human_reviewed") else "No"}')
                st.write(f'**Reviewer:** {need.get("reviewer") or "Not assigned"}')

    with evidence_tab:
        if not evidence:
            st.info("No evidence is currently linked to this need.")
        else:
            for _, row in pd.DataFrame(evidence).iterrows():
                with st.container(border=True):
                    header, action = st.columns([5, 1.2])
                    with header:
                        st.markdown(f'**{row["evidence_code"]}**')
                        st.caption(
                            f'{row.get("organization_name") or "Unknown organization"} · '
                            f'{row.get("event_year") or "Unknown year"} · '
                            f'{row.get("evidence_type") or "Evidence"}'
                        )
                    with action:
                        if st.button(
                            "Open",
                            key=f'open_evidence_{row["evidence_code"]}',
                            use_container_width=True,
                        ):
                            goto_evidence(row["evidence_code"])

                    st.write(row["original_statement"])
                    if row.get("source_title"):
                        st.caption(f'Source: {row["source_title"]}')
                    if row.get("source_location"):
                        st.caption(f'Location: {row["source_location"]}')

    with organizations_tab:
        if not organizations:
            st.info("No organizations are linked through supporting evidence.")
        else:
            st.caption("Organizations are derived from the evidence linked to this need.")
            for organization in organizations:
                related = [
                    row for row in evidence
                    if row.get("organization_name") == organization
                ]
                with st.container(border=True):
                    st.subheader(organization)
                    st.write(f"Supporting evidence statements: **{len(related)}**")
                    years = sorted({row.get("event_year") for row in related if row.get("event_year")})
                    if years:
                        st.caption("Years represented: " + ", ".join(str(year) for year in years))

    with implementation_tab:
        if not artifacts:
            st.info(
                "No implementation artifacts are linked to this need yet. "
                "Run the matcher or add a reviewed match to populate this tab."
            )
        else:
            confirmed = sum(1 for item in artifacts if item.get("review_status") == "Confirmed")
            pending = sum(1 for item in artifacts if item.get("review_status") == "Pending")
            uncertain = sum(1 for item in artifacts if item.get("review_status") == "Uncertain")
            rejected = sum(1 for item in artifacts if item.get("review_status") == "Rejected")

            summary = st.columns(4)
            summary[0].metric("Confirmed", confirmed)
            summary[1].metric("Pending", pending)
            summary[2].metric("Uncertain", uncertain)
            summary[3].metric("Rejected", rejected)

            st.caption(
                "Artifacts are linked to the canonical need. Supporting evidence connects indirectly through the need."
            )

            for artifact in artifacts:
                with st.container(border=True):
                    heading, status_col, link_col = st.columns([5, 1.4, 1.4])

                    with heading:
                        number = (
                            f' #{artifact["external_number"]}'
                            if artifact.get("external_number") is not None
                            else ""
                        )
                        st.markdown(
                            f'### {artifact.get("tool_name") or artifact.get("tool_code")} · '
                            f'{artifact.get("artifact_type", "artifact").replace("_", " ").title()}{number}'
                        )
                        st.write(artifact.get("title") or "Untitled artifact")
                        st.caption(
                            f'{artifact.get("owner_name")}/{artifact.get("repository_name")} · '
                            f'Artifact state: {artifact.get("state") or "Unknown"}'
                        )

                    with status_col:
                        st.metric("Match score", _score_percent(artifact.get("overall_score")))
                        st.caption(f'Review: {artifact.get("review_status") or "Pending"}')

                    with link_col:
                        if artifact.get("external_url"):
                            st.link_button(
                                "Open GitHub",
                                artifact["external_url"],
                                use_container_width=True,
                            )

                    st.write(
                        f'**Relationship:** {artifact.get("relationship_type") or "Potential Match"}'
                    )
                    if artifact.get("match_explanation"):
                        st.caption(artifact["match_explanation"])

                    with st.expander("Review this implementation match"):
                        current_relationship = artifact.get("relationship_type") or "Potential Match"
                        if current_relationship not in RELATIONSHIP_OPTIONS:
                            current_relationship = "Potential Match"

                        current_review_status = artifact.get("review_status") or "Pending"
                        if current_review_status not in REVIEW_STATUS_OPTIONS:
                            current_review_status = "Pending"

                        relationship = st.selectbox(
                            "Relationship",
                            RELATIONSHIP_OPTIONS,
                            index=RELATIONSHIP_OPTIONS.index(current_relationship),
                            key=f'relationship_{artifact["match_id"]}',
                        )
                        review_status = st.selectbox(
                            "Review status",
                            REVIEW_STATUS_OPTIONS,
                            index=REVIEW_STATUS_OPTIONS.index(current_review_status),
                            key=f'review_status_{artifact["match_id"]}',
                        )
                        reviewer = st.text_input(
                            "Reviewer",
                            value="local-demo",
                            key=f'match_reviewer_{artifact["match_id"]}',
                        )
                        review_notes = st.text_area(
                            "Review notes",
                            key=f'match_notes_{artifact["match_id"]}',
                        )

                        if st.button(
                            "Save implementation review",
                            key=f'save_match_{artifact["match_id"]}',
                            type="primary",
                        ):
                            api.patch(
                                f'/matches/{artifact["match_id"]}',
                                {
                                    "relationship_type": relationship,
                                    "review_status": review_status,
                                    "reviewer": reviewer,
                                    "review_notes": review_notes,
                                },
                            )
                            st.success("Implementation review saved.")
                            st.rerun()

    with review_tab:
        canonical = st.text_area(
            "Canonical wording",
            value=need["canonical_need"],
            height=145,
        )
        desired_outcome = st.text_area(
            "Desired outcome",
            value=need.get("desired_outcome") or "",
            height=100,
        )

        current_status = need.get("lifecycle_status") or "Candidate"
        if current_status not in STATUS_OPTIONS:
            current_status = "Candidate"

        current_priority = need.get("priority") or "Unassigned"
        if current_priority not in PRIORITY_OPTIONS:
            current_priority = "Unassigned"

        col1, col2, col3 = st.columns(3)
        status = col1.selectbox(
            "Status",
            STATUS_OPTIONS,
            index=STATUS_OPTIONS.index(current_status),
        )
        priority = col2.selectbox(
            "Priority",
            PRIORITY_OPTIONS,
            index=PRIORITY_OPTIONS.index(current_priority),
        )
        reviewed = col3.checkbox(
            "Human reviewed",
            value=bool(need.get("human_reviewed")),
        )

        reviewer = st.text_input(
            "Reviewer",
            value=need.get("reviewer") or "local-demo",
        )
        notes = st.text_area(
            "Review notes",
            value=need.get("notes") or "",
            height=110,
        )

        if st.button("Save review", type="primary"):
            api.patch(
                f"/needs/{need_code}",
                {
                    "canonical_need": canonical,
                    "desired_outcome": desired_outcome,
                    "lifecycle_status": status,
                    "priority": priority,
                    "human_reviewed": reviewed,
                    "reviewer": reviewer,
                    "notes": notes,
                },
            )
            st.success("Review saved.")
            st.rerun()

    st.divider()
    needs_link()
