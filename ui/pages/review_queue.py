import pandas as pd
import streamlit as st

import api_client as api
from navigation import goto_need
from styles import page_header


def render() -> None:
    page_header(
        "Need Quality Review",
        "Review possible grammar, clarity, and structure issues before "
        "marking canonical needs as authoritative.",
    )

    left, right = st.columns([2, 1])
    with left:
        quality_filter = st.selectbox(
            "Quality status",
            ["Needs attention", "High priority", "Review", "Clear"],
            index=0,
        )
    with right:
        include_reviewed = st.checkbox(
            "Include already reviewed needs",
            value=True,
        )

    parameters = {"limit": 1000}
    if not include_reviewed:
        parameters["reviewed"] = False

    records = api.get(
        "/needs/quality-review",
        parameters,
    )

    if quality_filter == "Needs attention":
        records = [
            record
            for record in records
            if record["quality_status"] != "Clear"
        ]
    else:
        records = [
            record
            for record in records
            if record["quality_status"] == quality_filter
        ]

    if not records:
        st.success("No canonical needs match this quality filter.")
        return

    high_priority = sum(
        record["quality_status"] == "High priority"
        for record in records
    )
    metric_one, metric_two, metric_three = st.columns(3)
    metric_one.metric("Needs shown", len(records))
    metric_two.metric("High priority", high_priority)
    metric_three.metric(
        "Already reviewed",
        sum(bool(record.get("human_reviewed")) for record in records),
    )

    st.caption(
        "Flags are deterministic review aids, not automatic grammar "
        "corrections. Open a need to compare its wording with the original "
        "evidence before editing it."
    )

    dataframe = pd.DataFrame(records)
    dataframe["quality_flags_display"] = dataframe["quality_flags"].apply(
        lambda values: "; ".join(values)
    )

    visible_columns = [
        "quality_status",
        "need_code",
        "canonical_need",
        "quality_flags_display",
        "need_category",
        "evidence_count",
        "organization_count",
        "signal_score",
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
            "quality_status": st.column_config.TextColumn(
                "Quality",
                width="small",
            ),
            "need_code": st.column_config.TextColumn(
                "Need ID",
                width="small",
            ),
            "canonical_need": st.column_config.TextColumn(
                "Canonical need",
                width="large",
            ),
            "quality_flags_display": st.column_config.TextColumn(
                "Review flags",
                width="large",
            ),
            "need_category": st.column_config.TextColumn(
                "Category",
                width="medium",
            ),
            "evidence_count": st.column_config.NumberColumn(
                "Evidence",
                format="%d",
            ),
            "organization_count": st.column_config.NumberColumn(
                "Organizations",
                format="%d",
            ),
            "signal_score": st.column_config.ProgressColumn(
                "Signal",
                min_value=0,
                max_value=100,
                format="%d",
            ),
            "human_reviewed": st.column_config.CheckboxColumn(
                "Reviewed",
            ),
        },
    )

    if event.selection.rows:
        selected_index = event.selection.rows[0]
        selected = records[selected_index]
        goto_need(selected["need_code"])
