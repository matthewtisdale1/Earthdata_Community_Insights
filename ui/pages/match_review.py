import streamlit as st

import api_client as api
from styles import page_header

RELATIONSHIPS = [
    "Tracks Need",
    "Proposes Solution",
    "Partially Addresses",
    "Fully Addresses",
    "Implements",
    "Documents",
    "Unrelated",
]


def render() -> None:
    page_header(
        "Implementation Match Review",
        "Review candidate links between community needs and imported implementation artifacts.",
    )

    filters = st.columns([1, 1, 1])
    minimum_score = filters[0].slider("Minimum score", 0.0, 1.0, 0.22, 0.01)
    tool_code = filters[1].selectbox(
        "Tool",
        ["", "EARTHDATA_SEARCH", "WORLDVIEW", "GIBS", "CMR", "HARMONY"],
        format_func=lambda value: value or "All tools",
    )
    reviewer = filters[2].text_input("Reviewer", value="local-demo")

    matches = api.get(
        "/matches/pending",
        {"minimum_score": minimum_score, "tool_code": tool_code, "limit": 250},
    )

    st.metric("Pending candidates", len(matches))
    if not matches:
        st.info("No pending candidates match the current filters. Run the matcher or lower the score threshold.")
        return

    for match in matches:
        with st.container(border=True):
            left, right = st.columns([1, 1], gap="large")
            with left:
                st.caption(f'{match["need_code"]} · {match.get("need_category") or "Uncategorized"}')
                st.subheader(match["canonical_need"])
            with right:
                number = f' #{match["external_number"]}' if match.get("external_number") else ""
                st.caption(f'{match["tool_name"]} · {match["artifact_type"]}{number} · {match.get("state") or "unknown"}')
                st.subheader(match["title"])
                if match.get("external_url"):
                    st.link_button("Open artifact", match["external_url"])

            score = float(match.get("overall_score") or 0)
            st.progress(score, text=f"Candidate score: {score:.0%}")
            st.caption(match.get("match_explanation") or "No explanation recorded.")

            relationship = st.selectbox(
                "Relationship",
                RELATIONSHIPS,
                key=f'relationship_{match["match_id"]}',
            )
            notes = st.text_input("Review notes", key=f'notes_{match["match_id"]}')
            actions = st.columns(4)

            def save(status: str, selected_relationship: str = relationship) -> None:
                api.patch(
                    f'/matches/{match["match_id"]}',
                    {
                        "relationship_type": selected_relationship,
                        "review_status": status,
                        "reviewer": reviewer or "local-demo",
                        "review_notes": notes or None,
                    },
                )
                st.rerun()

            if actions[0].button("Confirm", key=f'confirm_{match["match_id"]}', use_container_width=True):
                save("Confirmed")
            if actions[1].button("Reject", key=f'reject_{match["match_id"]}', use_container_width=True):
                save("Rejected", "Unrelated")
            if actions[2].button("Uncertain", key=f'uncertain_{match["match_id"]}', use_container_width=True):
                save("Uncertain")
            if actions[3].button("Keep pending", key=f'pending_{match["match_id"]}', use_container_width=True):
                save("Pending")
