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
from pages.tool_detail import render as render_tool_detail
from pages.tools import render as render_tools
from styles import apply_styles


st.set_page_config(
    page_title="Earthdata Community Insights",
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

tools = st.Page(
    render_tools,
    title="Earthdata Tools",
    icon=":material/apps:",
    url_path="tools",
)

tool_detail = st.Page(
    render_tool_detail,
    title="Tool Details",
    icon=":material/build:",
    url_path="tool-detail",
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
        "tools": tools,
        "tool_detail": tool_detail,
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
            tools,
            organizations,
            sources,
        ],
        "Curation": [
            review_queue,
        ],
        "Details": [
            need_detail,
            evidence_detail,
            tool_detail,
        ],
    },
    expanded=True,
)


with st.sidebar:
    st.markdown("## NASA Earthdata")
    st.caption("Community Insights Prototype")
    st.divider()
    st.caption(
        "Explore recurring community needs, supporting evidence, and the Earthdata tools that may address them."
    )


navigation.run()
