import pandas as pd
import streamlit as st

import api_client as api
from navigation import goto_evidence
from styles import page_header


def render() -> None:
    page_header(
        "Evidence",
        "Browse original statements that "
        "support the canonical community needs.",
    )

    left, right = st.columns(
        [4, 1]
    )

    search = left.text_input(
        "Search evidence",
        placeholder=(
            "Search statements, "
            "organizations, or IDs"
        ),
    )

    reviewed_option = (
        right.selectbox(
            "Reviewed",
            [
                "All",
                "Yes",
                "No",
            ],
        )
    )

    params = {
        "q": search,
        "limit": 1000,
    }

    if reviewed_option != "All":
        params["reviewed"] = (
            reviewed_option == "Yes"
        )

    records = api.get(
        "/evidence",
        params,
    )

    st.caption(
        f"{len(records)} evidence records"
    )

    if not records:
        st.info(
            "No evidence matched the "
            "selected filters."
        )
        return

    dataframe = pd.DataFrame(
        records
    )

    visible_columns = [
        "evidence_code",
        "need_code",
        "original_statement",
        "organization_name",
        "event_year",
        "source_title",
        "human_reviewed",
    ]

    event = st.dataframe(
        dataframe[visible_columns],
        hide_index=True,
        use_container_width=True,
        height=650,
        selection_mode="single-row",
        on_select="rerun",
        column_config={
            "evidence_code":
                st.column_config.TextColumn(
                    "Evidence ID",
                    width="small",
                ),
            "need_code":
                st.column_config.TextColumn(
                    "Need ID",
                    width="small",
                ),
            "original_statement":
                st.column_config.TextColumn(
                    "Statement",
                    width="large",
                ),
            "organization_name":
                st.column_config.TextColumn(
                    "Organization",
                    width="medium",
                ),
            "event_year":
                st.column_config.NumberColumn(
                    "Year",
                    format="%d",
                ),
            "source_title":
                st.column_config.TextColumn(
                    "Source",
                    width="medium",
                ),
            "human_reviewed":
                st.column_config.CheckboxColumn(
                    "Reviewed",
                ),
        },
    )

    if event.selection.rows:
        selected_index = (
            event.selection.rows[0]
        )

        selected = records[
            selected_index
        ]

        goto_evidence(
            selected[
                "evidence_code"
            ]
        )
