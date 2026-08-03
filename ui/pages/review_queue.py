import pandas as pd
import streamlit as st

import api_client as api
from navigation import goto_need
from styles import page_header


def render() -> None:
    page_header(
        "Review Queue",
        "Review high-signal draft needs "
        "that have not yet been validated.",
    )

    records = api.get(
        "/needs",
        {
            "reviewed": False,
            "limit": 500,
        },
    )

    if not records:
        st.success(
            "All needs have been reviewed."
        )
        return

    st.metric(
        "Needs awaiting review",
        len(records),
    )

    dataframe = pd.DataFrame(
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
    ]

    event = st.dataframe(
        dataframe[visible_columns],
        hide_index=True,
        use_container_width=True,
        height=650,
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
                    "Draft canonical need",
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
