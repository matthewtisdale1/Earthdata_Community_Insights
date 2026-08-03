import pandas as pd
import streamlit as st

import api_client as api
from navigation import goto_need
from styles import page_header


def render() -> None:
    page_header(
        "Community Needs",
        "Search and explore canonical needs "
        "with their supporting evidence.",
    )

    with st.container(
        border=True
    ):
        col1, col2, col3, col4 = (
            st.columns(
                [3, 2, 1.5, 1.5]
            )
        )

        search = col1.text_input(
            "Search",
            placeholder=(
                "Cloud, GIS, metadata, "
                "training..."
            ),
        )

        category = col2.text_input(
            "Category",
            placeholder=(
                "Optional exact category"
            ),
        )

        reviewed_option = (
            col3.selectbox(
                "Reviewed",
                [
                    "All",
                    "Yes",
                    "No",
                ],
            )
        )

        minimum_evidence = (
            col4.number_input(
                "Minimum evidence",
                min_value=0,
                value=0,
                step=1,
            )
        )

    params = {
        "q": search,
        "category": category,
        "limit": 500,
    }

    if reviewed_option != "All":
        params["reviewed"] = (
            reviewed_option == "Yes"
        )

    records = api.get(
        "/needs",
        params,
    )

    records = [
        record
        for record in records
        if (
            record.get(
                "evidence_count",
                0,
            )
            >= minimum_evidence
        )
    ]

    st.caption(
        f"{len(records)} matching needs"
    )

    if not records:
        st.info(
            "No needs matched the "
            "selected filters."
        )
        return

    table = pd.DataFrame(
        records
    )

    visible_columns = [
        "need_code",
        "canonical_need",
        "need_category",
        "evidence_count",
        "organization_count",
        "year_count",
        "signal_score",
        "human_reviewed",
    ]

    event = st.dataframe(
        table[visible_columns],
        hide_index=True,
        use_container_width=True,
        height=620,
        selection_mode="single-row",
        on_select="rerun",
        column_config={
            "need_code":
                st.column_config.TextColumn(
                    "Need ID",
                    width="small",
                ),
            "canonical_need":
                st.column_config.TextColumn(
                    "Canonical need",
                    width="large",
                ),
            "need_category":
                st.column_config.TextColumn(
                    "Category",
                    width="medium",
                ),
            "evidence_count":
                st.column_config.NumberColumn(
                    "Evidence",
                    format="%d",
                ),
            "organization_count":
                st.column_config.NumberColumn(
                    "Organizations",
                    format="%d",
                ),
            "year_count":
                st.column_config.NumberColumn(
                    "Years",
                    format="%d",
                ),
            "signal_score":
                st.column_config.ProgressColumn(
                    "Signal",
                    min_value=0,
                    max_value=100,
                    format="%d",
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

        goto_need(
            selected["need_code"]
        )
