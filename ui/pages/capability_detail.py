import pandas as pd
import streamlit as st

import api_client as api
from navigation import capabilities_link, goto_need, goto_tool
from styles import breadcrumb, page_header


def render_solution_card(item: dict) -> None:
    with st.container(border=True):
        heading = item.get('title') or 'Official source'
        st.markdown(f"### {heading}")
        st.caption(
            f"{item.get('tool_name') or 'Earthdata tool'} · "
            f"{item.get('evidence_role') or 'Solution evidence'} · "
            f"{item.get('evidence_type') or 'source'}"
        )
        if item.get('description'):
            st.write(item['description'])
        if item.get('supporting_excerpt'):
            st.info(item['supporting_excerpt'], icon=':material/fact_check:')
        meta = st.columns(3)
        meta[0].write(f"**Review:** {item.get('review_status') or 'Pending'}")
        meta[1].write(f"**Version:** {item.get('version_label') or 'Current documentation'}")
        meta[2].write(f"**Verified:** {item.get('last_verified_at') or 'Not recorded'}")
        if item.get('source_url'):
            st.link_button('Open official source', item['source_url'])


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
    solution_evidence = detail.get('solution_evidence', [])
    engineering_artifacts = detail.get('engineering_artifacts', [])

    breadcrumb('Capabilities › Capability Details')
    page_header(capability['capability_name'], capability.get('description') or 'Earthdata capability')

    metrics = st.columns(5)
    metrics[0].metric('Community needs', int(capability.get('need_count') or 0))
    metrics[1].metric('Evidence statements', int(capability.get('evidence_count') or 0))
    metrics[2].metric('Organizations', int(capability.get('organization_count') or 0))
    metrics[3].metric('Earthdata tools', int(capability.get('tool_count') or 0))
    metrics[4].metric('Official sources', len(solution_evidence))

    overview_tab, solutions_tab, needs_tab, tools_tab, engineering_tab = st.tabs([
        'Overview',
        f'Solutions ({len(solution_evidence)})',
        f'Community Needs ({len(needs)})',
        f'Tools ({len(tools)})',
        f'Engineering ({len(engineering_artifacts)})',
    ])

    with overview_tab:
        st.subheader('Capability definition')
        st.write(capability.get('description') or 'No description recorded.')
        st.write(f"**Category:** {capability.get('category') or 'Uncategorized'}")
        st.write(f"**Maturity:** {capability.get('maturity') or 'Not assessed'}")
        st.info(
            'Official documentation and release information are treated as the primary proof that a capability is available. '
            'Issues and pull requests are retained separately as engineering provenance.',
            icon=':material/menu_book:',
        )

    with solutions_tab:
        if not solution_evidence:
            st.info('No official documentation, release notes, API references, or tutorials are linked yet.')
        else:
            roles = []
            for item in solution_evidence:
                role = item.get('evidence_role') or 'Other'
                if role not in roles:
                    roles.append(role)
            for role in roles:
                st.subheader(role)
                for item in solution_evidence:
                    if (item.get('evidence_role') or 'Other') == role:
                        render_solution_card(item)

    with needs_tab:
        if not needs:
            st.info('No community needs are linked yet.')
        for need in needs:
            with st.container(border=True):
                cols = st.columns([5, 1])
                with cols[0]:
                    st.markdown(f"**{need['need_code']}** — {need['canonical_need']}")
                    st.caption(
                        f"{need.get('review_status')} · "
                        f"{need.get('evidence_count', 0)} evidence statements · "
                        f"{need.get('organization_count', 0)} organizations"
                    )
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
                    st.caption(
                        f"{tool.get('support_level') or 'Support not assessed'} · "
                        f"{'Reviewed' if tool.get('reviewed') else 'Needs review'}"
                    )
                with cols[1]:
                    if st.button('Open tool', key=f"cap_tool_{tool['tool_code']}", use_container_width=True):
                        goto_tool(tool['tool_code'])

    with engineering_tab:
        st.caption('Secondary engineering provenance. These records do not by themselves prove that a user-facing capability is currently supported.')
        if not engineering_artifacts:
            st.info('No related engineering artifacts are linked through capability-related needs.')
        else:
            st.dataframe(
                pd.DataFrame(engineering_artifacts),
                hide_index=True,
                use_container_width=True,
                column_config={'external_url': st.column_config.LinkColumn('Artifact')},
            )

    st.divider()
    capabilities_link()
