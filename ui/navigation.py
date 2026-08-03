from typing import Any

import streamlit as st


def register_pages(pages: dict[str, Any]) -> None:
    st.session_state["registered_pages"] = pages


def _get_page(name: str):
    pages = st.session_state.get(
        "registered_pages",
        {},
    )

    if name not in pages:
        raise RuntimeError(
            f"Navigation page '{name}' has not been registered."
        )

    return pages[name]


def goto_dashboard() -> None:
    st.switch_page(
        _get_page("dashboard")
    )


def goto_needs() -> None:
    st.switch_page(
        _get_page("needs")
    )


def goto_need(need_code: str) -> None:
    st.session_state[
        "selected_need_code"
    ] = need_code

    st.switch_page(
        _get_page("need_detail")
    )


def goto_evidence_list() -> None:
    st.switch_page(
        _get_page("evidence")
    )


def goto_evidence(
    evidence_code: str,
) -> None:
    st.session_state[
        "selected_evidence_code"
    ] = evidence_code

    st.switch_page(
        _get_page("evidence_detail")
    )


def goto_organizations() -> None:
    st.switch_page(
        _get_page("organizations")
    )


def goto_sources() -> None:
    st.switch_page(
        _get_page("sources")
    )


def goto_review_queue() -> None:
    st.switch_page(
        _get_page("review_queue")
    )


def needs_link(
    label: str = "Back to all needs",
    icon: str = ":material/arrow_back:",
) -> None:
    st.page_link(
        _get_page("needs"),
        label=label,
        icon=icon,
    )


def evidence_link(
    label: str = "Back to evidence",
    icon: str = ":material/arrow_back:",
) -> None:
    st.page_link(
        _get_page("evidence"),
        label=label,
        icon=icon,
    )
