import pandas as pd
import streamlit as st

import api_client as api
from navigation import (
    goto_evidence,
    needs_link,
)
from styles import (
    breadcrumb,
    page_header,
)


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


def render() -> None:
    need_code = (
        st.session_state.get(
            "selected_need_code"
        )
    )

    if not need_code:
        st.warning(
            "No need was selected."
        )

        needs_link(
            label="Return to Needs"
        )
        return

    detail = api.get(
        f"/needs/{need_code}"
    )

    need = detail["need"]
    evidence = detail["evidence"]

    breadcrumb(
        "Community Needs › Need Details"
    )

    page_header(
        need_code,
        need["canonical_need"],
    )

    metric_columns = st.columns(6)

    metric_columns[0].metric(
        "Signal",
        int(
            need.get(
                "signal_score"
            )
            or 0
        ),
    )

    metric_columns[1].metric(
        "Evidence",
        need.get(
            "evidence_count",
            0,
        ),
    )

    metric_columns[2].metric(
        "Organizations",
        need.get(
            "organization_count",
            0,
        ),
    )

    metric_columns[3].metric(
        "Years",
        need.get(
            "year_count",
            0,
        ),
    )

    metric_columns[4].metric(
        "First seen",
        need.get(
            "first_seen_year"
        )
        or "—",
    )

    metric_columns[5].metric(
        "Last seen",
        need.get(
            "last_seen_year"
        )
        or "—",
    )

    overview_tab, evidence_tab, review_tab = (
        st.tabs(
            [
                "Overview",
                (
                    f"Evidence "
                    f"({len(evidence)})"
                ),
                "Review",
            ]
        )
    )

    with overview_tab:
        left, right = st.columns(
            [2, 1],
            gap="large",
        )

        with left:
            st.subheader(
                "Canonical need"
            )

            st.write(
                need["canonical_need"]
            )

            st.subheader(
                "Desired outcome"
            )

            if need.get(
                "desired_outcome"
            ):
                st.write(
                    need[
                        "desired_outcome"
                    ]
                )
            else:
                st.info(
                    "A desired outcome has "
                    "not yet been recorded."
                )

            if need.get("notes"):
                st.subheader("Notes")
                st.write(
                    need["notes"]
                )

        with right:
            with st.container(
                border=True
            ):
                st.markdown(
                    "#### Classification"
                )

                st.write(
                    f'**Category:** '
                    f'{need.get("need_category") or "Uncategorized"}'
                )

                st.write(
                    f'**Status:** '
                    f'{need.get("lifecycle_status") or "Candidate"}'
                )

                st.write(
                    f'**Priority:** '
                    f'{need.get("priority") or "Unassigned"}'
                )

                st.write(
                    f'**Trend:** '
                    f'{need.get("trend") or "Unknown"}'
                )

                st.write(
                    f'**Reviewed:** '
                    f'{"Yes" if need.get("human_reviewed") else "No"}'
                )

                st.write(
                    f'**Reviewer:** '
                    f'{need.get("reviewer") or "Not assigned"}'
                )

    with evidence_tab:
        if not evidence:
            st.info(
                "No evidence is currently "
                "linked to this need."
            )
        else:
            evidence_df = pd.DataFrame(
                evidence
            )

            for _, row in (
                evidence_df.iterrows()
            ):
                with st.container(
                    border=True
                ):
                    header, action = (
                        st.columns(
                            [5, 1.2]
                        )
                    )

                    with header:
                        st.markdown(
                            f'**{row["evidence_code"]}**'
                        )

                        st.caption(
                            f'{row.get("organization_name") or "Unknown organization"} · '
                            f'{row.get("event_year") or "Unknown year"} · '
                            f'{row.get("evidence_type") or "Evidence"}'
                        )

                    with action:
                        if st.button(
                            "Open",
                            key=(
                                f'open_evidence_'
                                f'{row["evidence_code"]}'
                            ),
                            use_container_width=True,
                        ):
                            goto_evidence(
                                row[
                                    "evidence_code"
                                ]
                            )

                    st.write(
                        row[
                            "original_statement"
                        ]
                    )

                    if row.get(
                        "source_title"
                    ):
                        st.caption(
                            f'Source: '
                            f'{row["source_title"]}'
                        )

                    if row.get(
                        "source_location"
                    ):
                        st.caption(
                            f'Location: '
                            f'{row["source_location"]}'
                        )

    with review_tab:
        canonical = st.text_area(
            "Canonical wording",
            value=(
                need[
                    "canonical_need"
                ]
            ),
            height=145,
        )

        desired_outcome = (
            st.text_area(
                "Desired outcome",
                value=(
                    need.get(
                        "desired_outcome"
                    )
                    or ""
                ),
                height=100,
            )
        )

        current_status = (
            need.get(
                "lifecycle_status"
            )
            or "Candidate"
        )

        if (
            current_status
            not in STATUS_OPTIONS
        ):
            current_status = (
                "Candidate"
            )

        current_priority = (
            need.get("priority")
            or "Unassigned"
        )

        if (
            current_priority
            not in PRIORITY_OPTIONS
        ):
            current_priority = (
                "Unassigned"
            )

        col1, col2, col3 = (
            st.columns(3)
        )

        status = col1.selectbox(
            "Status",
            STATUS_OPTIONS,
            index=STATUS_OPTIONS.index(
                current_status
            ),
        )

        priority = col2.selectbox(
            "Priority",
            PRIORITY_OPTIONS,
            index=PRIORITY_OPTIONS.index(
                current_priority
            ),
        )

        reviewed = col3.checkbox(
            "Human reviewed",
            value=bool(
                need.get(
                    "human_reviewed"
                )
            ),
        )

        reviewer = st.text_input(
            "Reviewer",
            value=(
                need.get("reviewer")
                or "local-demo"
            ),
        )

        notes = st.text_area(
            "Review notes",
            value=(
                need.get("notes")
                or ""
            ),
            height=110,
        )

        if st.button(
            "Save review",
            type="primary",
        ):
            api.patch(
                f"/needs/{need_code}",
                {
                    "canonical_need":
                        canonical,
                    "desired_outcome":
                        desired_outcome,
                    "lifecycle_status":
                        status,
                    "priority":
                        priority,
                    "human_reviewed":
                        reviewed,
                    "reviewer":
                        reviewer,
                    "notes":
                        notes,
                },
            )

            st.success(
                "Review saved."
            )

            st.rerun()

    st.divider()
    needs_link()
