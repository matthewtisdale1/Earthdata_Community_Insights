import html

import streamlit as st

import api_client as api
from navigation import (
    evidence_link,
    goto_need,
)
from styles import (
    breadcrumb,
    page_header,
)


def render() -> None:
    evidence_code = (
        st.session_state.get(
            "selected_evidence_code"
        )
    )

    if not evidence_code:
        st.warning(
            "No evidence record "
            "was selected."
        )

        evidence_link(
            label="Return to Evidence"
        )
        return

    evidence = api.get(
        f"/evidence/{evidence_code}"
    )

    breadcrumb(
        "Evidence › Evidence Details"
    )

    page_header(
        evidence_code,
        evidence.get(
            "evidence_type"
        )
        or "Community evidence",
    )

    left, right = st.columns(
        [2, 1],
        gap="large",
    )

    with left:
        st.subheader(
            "Original statement"
        )

        safe_statement = (
            html.escape(
                evidence[
                    "original_statement"
                ]
            )
        )

        st.markdown(
            f"""
            <div class="source-quote">
                <p>{safe_statement}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.subheader(
            "Normalized statement"
        )

        st.write(
            evidence.get(
                "normalized_statement"
            )
            or (
                "No normalized statement "
                "has been recorded."
            )
        )

        if evidence.get(
            "context_rationale"
        ):
            st.subheader(
                "Context and rationale"
            )

            st.write(
                evidence[
                    "context_rationale"
                ]
            )

    with right:
        with st.container(
            border=True
        ):
            st.markdown(
                "#### Evidence details"
            )

            st.write(
                f'**Organization:** '
                f'{evidence.get("organization_name") or "Unknown"}'
            )

            st.write(
                f'**Year:** '
                f'{evidence.get("event_year") or "Unknown"}'
            )

            st.write(
                f'**Source:** '
                f'{evidence.get("source_title") or "Unknown"}'
            )

            st.write(
                f'**Location:** '
                f'{evidence.get("source_location") or "Not recorded"}'
            )

            st.write(
                f'**Community:** '
                f'{evidence.get("user_community") or "Not classified"}'
            )

            confidence = evidence.get(
                "match_confidence"
            )

            if confidence is not None:
                st.write(
                    f'**Match confidence:** '
                    f'{float(confidence):.0%}'
                )
            else:
                st.write(
                    "**Match confidence:** "
                    "Not available"
                )

            st.write(
                f'**Reviewed:** '
                f'{"Yes" if evidence.get("human_reviewed") else "No"}'
            )

    if evidence.get(
        "need_code"
    ):
        st.subheader(
            "Linked canonical need"
        )

        with st.container(
            border=True
        ):
            st.markdown(
                f'### {evidence["need_code"]}'
            )

            st.write(
                evidence.get(
                    "canonical_need"
                )
                or (
                    "Canonical wording "
                    "is unavailable."
                )
            )

            if st.button(
                "Open linked need",
                type="primary",
                use_container_width=True,
            ):
                goto_need(
                    evidence[
                        "need_code"
                    ]
                )

    else:
        st.warning(
            "This evidence is not currently "
            "linked to a canonical need."
        )

    st.divider()
    evidence_link()
