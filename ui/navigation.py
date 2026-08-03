from typing import Any

import streamlit as st


def register_pages(pages: dict[str, Any]) -> None:
    st.session_state['registered_pages'] = pages


def _get_page(name: str):
    pages = st.session_state.get('registered_pages', {})
    if name not in pages:
        raise RuntimeError(f"Navigation page '{name}' has not been registered.")
    return pages[name]


def goto_dashboard(): st.switch_page(_get_page('dashboard'))
def goto_needs(): st.switch_page(_get_page('needs'))
def goto_need(need_code: str):
    st.session_state['selected_need_code'] = need_code
    st.switch_page(_get_page('need_detail'))
def goto_evidence_list(): st.switch_page(_get_page('evidence'))
def goto_evidence(evidence_code: str):
    st.session_state['selected_evidence_code'] = evidence_code
    st.switch_page(_get_page('evidence_detail'))
def goto_tools(): st.switch_page(_get_page('tools'))
def goto_tool(tool_code: str):
    st.session_state['selected_tool_code'] = tool_code
    st.switch_page(_get_page('tool_detail'))
def goto_capabilities(): st.switch_page(_get_page('capabilities'))
def goto_capability(capability_code: str):
    st.session_state['selected_capability_code'] = capability_code
    st.switch_page(_get_page('capability_detail'))
def goto_organizations(): st.switch_page(_get_page('organizations'))
def goto_sources(): st.switch_page(_get_page('sources'))
def goto_review_queue(): st.switch_page(_get_page('review_queue'))


def needs_link(label='Back to all needs', icon=':material/arrow_back:'):
    st.page_link(_get_page('needs'), label=label, icon=icon)
def evidence_link(label='Back to evidence', icon=':material/arrow_back:'):
    st.page_link(_get_page('evidence'), label=label, icon=icon)
def tools_link(label='Back to Earthdata Tools', icon=':material/arrow_back:'):
    st.page_link(_get_page('tools'), label=label, icon=icon)
def capabilities_link(label='Back to Capabilities', icon=':material/arrow_back:'):
    st.page_link(_get_page('capabilities'), label=label, icon=icon)
