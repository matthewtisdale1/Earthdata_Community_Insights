import pandas as pd
import streamlit as st

import api_client as api
from navigation import capabilities_link, goto_need, goto_tool
from styles import breadcrumb, page_header


def render() -> None:
    code = st.session_state.get('selected_capability_code')
    if not code:
        st.warning('No capability was selected.')
        capabilities_link()
        return

    detail = api.get(f'/capabilities/{code}')
    capability = detail['capability']
    tools = detail['tools']
    needs = detail['needs']
    artifacts = detail['artifacts']

    breadcrumb('Capabilities › Capability Details')
    page_header(capability['capability_name'], capability.get('description') or 'Earthdata capability')

    metrics = st.columns(4)
    metrics[0].metric('Community needs', int(capability.get('need_count') or 0))
    metrics[1].metric('Evidence statements', int(capability.get('evidence_count') or 0))
    metrics[2].metric('Organizations', int(capability.get('organization_count') or 0))
    metrics[3].metric('Earthdata tools', int(capability.get('tool_count') or 0))

    overview_tab, needs_tab, tools_tab, implementation_tab = st.tabs([
        'Overview', f'Community Needs ({len(needs)})', f'Tools ({len(tools)})', f'Implementation ({len(artifacts)})'
    ])

    with overview_tab:
        st.subheader('Capability definition')
        st.write(capability.get('description') or 'No description recorded.')
        st.write(f"**Category:** {capability.get('category') or 'Uncategorized'}")
        st.write(f"**Maturity:** {capability.get('maturity') or 'Not assessed'}")

    with needs_tab:
        if not needs:
            st.info('No community needs are linked yet.')
        for need in needs:
            with st.container(border=True):
                cols = st.columns([5, 1])
                with cols[0]:
                    st.markdown(f"**{need['need_code']}** — {need['canonical_need']}")
                    st.caption(f"{need.get('review_status')} · {need.get('evidence_count', 0)} evidence statements · {need.get('organization_count', 0)} organizations")
                with cols[1]:
                    if st.button('Open need', key=f"cap_need_{need['need_code']}", use_container_width=True):
                        goto_need(need['need_code'])

    with tools_tab:
        if not tools:
            st.info('No tools are linked yet.')
        for tool in tools:
            with st.container(border=True):
                cols = st.columns([5, 1])
                with cols[0]:
                    st.markdown(f"**{tool['tool_name']}**")
                    st.caption(f"{tool.get('support_level') or 'Support not assessed'} · {'Reviewed' if tool.get('reviewed') else 'Needs review'}")
                with cols[1]:
                    if st.button('Open tool', key=f"cap_tool_{tool['tool_code']}", use_container_width=True):
                        goto_tool(tool['tool_code'])

    with implementation_tab:
        if not artifacts:
            st.info('No implementation artifacts are linked through capability-related needs yet.')
        else:
            st.dataframe(pd.DataFrame(artifacts), hide_index=True, use_container_width=True,
                         column_config={'external_url': st.column_config.LinkColumn('Artifact')})

    st.divider()
    capabilities_link()
