import pandas as pd
import streamlit as st

import api_client as api
from styles import page_header


def render() -> None:
    page_header(
        "Organizations",
        "See which UWGs and organizations "
        "contributed the most evidence.",
    )

    records = api.get(
        "/organizations"
    )

    if not records:
        st.info(
            "No organization records "
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
        height=650,
        column_config={
            "organization_id":
                st.column_config.NumberColumn(
                    "ID",
                    format="%d",
                ),
            "organization_name":
                st.column_config.TextColumn(
                    "Organization",
                    width="large",
                ),
            "organization_type":
                st.column_config.TextColumn(
                    "Type",
                    width="medium",
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
            "first_seen_year":
                st.column_config.NumberColumn(
                    "First seen",
                    format="%d",
                ),
            "last_seen_year":
                st.column_config.NumberColumn(
                    "Last seen",
                    format="%d",
                ),
        },
    )
