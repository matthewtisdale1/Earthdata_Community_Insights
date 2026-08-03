import pandas as pd
import streamlit as st

import api_client as api
from styles import page_header


def render() -> None:
    page_header(
        "Sources",
        "Review the reports from which "
        "community evidence was extracted.",
    )

    records = api.get(
        "/sources"
    )

    if not records:
        st.info(
            "No source records "
            "are available."
        )
        return

    dataframe = pd.DataFrame(
        records
    )

    st.dataframe(
        dataframe,
        hide_index=True,
        use_container_width=True,
        height=600,
        column_config={
            "source_code":
                st.column_config.TextColumn(
                    "Source ID",
                    width="small",
                ),
            "source_title":
                st.column_config.TextColumn(
                    "Title",
                    width="large",
                ),
            "source_type":
                st.column_config.TextColumn(
                    "Type",
                    width="medium",
                ),
            "source_year":
                st.column_config.NumberColumn(
                    "Year",
                    format="%d",
                ),
            "file_name":
                st.column_config.TextColumn(
                    "File",
                    width="large",
                ),
            "evidence_count":
                st.column_config.NumberColumn(
                    "Evidence",
                    format="%d",
                ),
            "need_count":
                st.column_config.NumberColumn(
                    "Needs",
                    format="%d",
                ),
        },
    )
