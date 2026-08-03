import pandas as pd
import streamlit as st

import api_client as api
from navigation import goto_need
from styles import page_header


def render() -> None:
    page_header(
        "Community Signals",
        "Explore recurring needs heard across "
        "NASA Earthdata User Working Groups.",
    )

    summary = api.get(
        "/dashboard/summary"
    )

    totals = summary["totals"]

    metric_columns = st.columns(4)

    metric_columns[0].metric(
        "Canonical needs",
        totals.get("needs", 0),
    )

    metric_columns[1].metric(
        "Evidence statements",
        totals.get("evidence", 0),
    )

    metric_columns[2].metric(
        "Source reports",
        totals.get("sources", 0),
    )

    metric_columns[3].metric(
        "Organizations",
        totals.get("organizations", 0),
    )

    st.divider()

    left, right = st.columns(
        [1.05, 1],
        gap="large",
    )

    with left:
        st.subheader(
            "Needs by topic"
        )

        topics = pd.DataFrame(
            summary["topics"]
        )

        if topics.empty:
            st.info(
                "No topic information is available."
            )
        else:
            topics = topics.rename(
                columns={
                    "need_category": "Topic",
                    "need_count": "Needs",
                }
            )

            st.bar_chart(
                topics.set_index(
                    "Topic"
                )["Needs"],
                height=430,
            )

    with right:
        st.subheader(
            "Largest draft clusters"
        )

        st.caption(
            "These are automated draft groupings "
            "and should be reviewed before being "
            "treated as final community priorities."
        )

        needs = api.get(
            "/needs",
            {
                "limit": 10,
            },
        )

        if not needs:
            st.info(
                "No needs are currently available."
            )

        for need in needs:
            with st.container(
                border=True
            ):
                heading, score = st.columns(
                    [5, 1]
                )

                with heading:
                    st.markdown(
                        f'**{need["need_code"]}**'
                    )

                    st.write(
                        need["canonical_need"]
                    )

                    st.caption(
                        f'{need["evidence_count"]} evidence · '
                        f'{need["organization_count"]} organizations · '
                        f'{need["first_seen_year"] or "—"}–'
                        f'{need["last_seen_year"] or "—"}'
                    )

                with score:
                    st.metric(
                        "Signal",
                        int(
                            need.get(
                                "signal_score"
                            )
                            or 0
                        ),
                    )

                if st.button(
                    "Open need",
                    key=(
                        f'open_dashboard_'
                        f'{need["need_code"]}'
                    ),
                    use_container_width=True,
                ):
                    goto_need(
                        need["need_code"]
                    )
