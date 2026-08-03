import streamlit as st

from navigation import register_pages
from pages.dashboard import render as render_dashboard
from pages.evidence import render as render_evidence
from pages.evidence_detail import render as render_evidence_detail
from pages.need_detail import render as render_need_detail
from pages.needs import render as render_needs
from pages.organizations import render as render_organizations
from pages.review_queue import render as render_review_queue
from pages.sources import render as render_sources
from styles import apply_styles


st.set_page_config(
    page_title="UWG Community Needs",
    page_icon="🌎",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_styles()


dashboard = st.Page(
    render_dashboard,
    title="Community Signals",
    icon=":material/insights:",
    url_path="dashboard",
    default=True,
)

needs = st.Page(
    render_needs,
    title="Needs",
    icon=":material/hub:",
    url_path="needs",
)

need_detail = st.Page(
    render_need_detail,
    title="Need Details",
    icon=":material/description:",
    url_path="need-detail",
    visibility="hidden",
)

evidence = st.Page(
    render_evidence,
    title="Evidence",
    icon=":material/format_quote:",
    url_path="evidence",
)

evidence_detail = st.Page(
    render_evidence_detail,
    title="Evidence Details",
    icon=":material/article:",
    url_path="evidence-detail",
    visibility="hidden",
)

organizations = st.Page(
    render_organizations,
    title="Organizations",
    icon=":material/account_balance:",
    url_path="organizations",
)

sources = st.Page(
    render_sources,
    title="Sources",
    icon=":material/folder_open:",
    url_path="sources",
)

review_queue = st.Page(
    render_review_queue,
    title="Review Queue",
    icon=":material/rule:",
    url_path="review-queue",
)


register_pages(
    {
        "dashboard": dashboard,
        "needs": needs,
        "need_detail": need_detail,
        "evidence": evidence,
        "evidence_detail": evidence_detail,
        "organizations": organizations,
        "sources": sources,
        "review_queue": review_queue,
    }
)


navigation = st.navigation(
    {
        "Explore": [
            dashboard,
            needs,
            evidence,
            organizations,
            sources,
        ],
        "Curation": [
            review_queue,
        ],
        "Details": [
            need_detail,
            evidence_detail,
        ],
    },
    expanded=True,
)


with st.sidebar:
    st.markdown("## NASA Earthdata")
    st.caption(
        "Community Needs Prototype"
    )
    st.divider()

    st.caption(
        "Explore recurring community needs "
        "and their supporting evidence."
    )


navigation.run()
