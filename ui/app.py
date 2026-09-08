import os
import streamlit as st

from navigation import register_pages
from pages.dashboard import render as render_dashboard
from pages.evidence import render as render_evidence
from pages.evidence_detail import render as render_evidence_detail
from pages.match_review import render as render_match_review
from pages.need_detail import render as render_need_detail
from pages.needs import render as render_needs
from pages.organizations import render as render_organizations
from pages.review_queue import render as render_review_queue
from pages.sources import render as render_sources
from pages.tool_detail import render as render_tool_detail
from pages.tools import render as render_tools
from pages.capabilities import render as render_capabilities
from pages.capability_detail import render as render_capability_detail
from pages.planning import render as render_planning
from styles import apply_styles

st.set_page_config(page_title='Earthdata Community Insights', page_icon='🌎', layout='wide', initial_sidebar_state='expanded')
apply_styles()

dashboard = st.Page(render_dashboard, title='Community Signals', icon=':material/insights:', url_path='dashboard', default=True)
needs = st.Page(render_needs, title='Needs', icon=':material/hub:', url_path='needs')
need_detail = st.Page(render_need_detail, title='Need Details', icon=':material/description:', url_path='need-detail', visibility='hidden')
evidence = st.Page(render_evidence, title='Evidence', icon=':material/format_quote:', url_path='evidence')
evidence_detail = st.Page(render_evidence_detail, title='Evidence Details', icon=':material/article:', url_path='evidence-detail', visibility='hidden')
capabilities = st.Page(render_capabilities, title='Capabilities', icon=':material/category:', url_path='capabilities')
capability_detail = st.Page(render_capability_detail, title='Capability Details', icon=':material/account_tree:', url_path='capability-detail', visibility='hidden')
tools = st.Page(render_tools, title='Earthdata Tools', icon=':material/apps:', url_path='tools')
tool_detail = st.Page(render_tool_detail, title='Tool Details', icon=':material/build:', url_path='tool-detail', visibility='hidden')
organizations = st.Page(render_organizations, title='Organizations', icon=':material/account_balance:', url_path='organizations')
sources = st.Page(render_sources, title='Sources', icon=':material/folder_open:', url_path='sources')
review_queue = st.Page(render_review_queue, title='Need Review Queue', icon=':material/rule:', url_path='review-queue')
match_review = st.Page(render_match_review, title='Implementation Matches', icon=':material/compare_arrows:', url_path='implementation-matches')

planning = st.Page(render_planning, title='PI Planning & Outcomes', icon=':material/checklist:', url_path='planning')

register_pages({'dashboard': dashboard, 'needs': needs, 'need_detail': need_detail, 'evidence': evidence,
                'evidence_detail': evidence_detail, 'capabilities': capabilities, 'capability_detail': capability_detail,
                'tools': tools, 'tool_detail': tool_detail, 'organizations': organizations, 'sources': sources,
                'review_queue': review_queue, 'match_review': match_review})

navigation = st.navigation({
    'Community': [dashboard, needs, evidence, organizations],
    'Earthdata Ecosystem': [capabilities, tools],
    'Planning': [planning],
    'Curation': [sources, review_queue, match_review],
    'Details': [need_detail, evidence_detail, capability_detail, tool_detail],
}, expanded=True)

with st.sidebar:
    st.markdown('## NASA Earthdata')
    st.caption('Community Insights Prototype')
    dataset_mode = os.environ.get('DATASET_MODE', 'full').upper()
    if dataset_mode == 'DEMO':
        st.warning('DATASET: DEMO', icon=':material/science:')
    else:
        st.info('DATASET: FULL', icon=':material/database:')
    st.divider()
    st.caption('Trace community evidence through needs and capabilities to Earthdata tools and implementation artifacts.')

navigation.run()
