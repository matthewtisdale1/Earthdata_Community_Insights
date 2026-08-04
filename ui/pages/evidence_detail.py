import html

import streamlit as st

import api_client as api
from navigation import evidence_link, goto_need
from styles import breadcrumb, page_header


def render() -> None:
    evidence_code = st.session_state.get('selected_evidence_code')
    if not evidence_code:
        st.warning('No evidence record was selected.')
        evidence_link(label='Return to Evidence')
        return

    evidence = api.get(f'/evidence/{evidence_code}')
    breadcrumb('Curation › Evidence Review')
    page_header(evidence_code, evidence.get('evidence_type') or 'Community evidence')

    left, right = st.columns([2, 1], gap='large')
    with left:
        st.subheader('Original evidence')
        safe = html.escape(evidence['original_statement'])
        st.markdown(f'<div class="source-quote"><p>{safe}</p></div>', unsafe_allow_html=True)
        st.subheader('Curated interpretation')
        st.write(evidence.get('normalized_statement') or 'No normalized statement has been recorded.')
        if evidence.get('context_rationale'):
            st.write(evidence['context_rationale'])

        st.subheader('Review decision')
        with st.form('evidence_review'):
            decision = st.selectbox('Decision', ['Approve', 'Edit', 'Merge', 'Split', 'Research', 'Retire'])
            need_code = st.text_input('Canonical need ID', value=evidence.get('need_code') or '', placeholder='NEED-001')
            reviewer = st.text_input('Reviewer', value='local-reviewer')
            rationale = st.text_area('Rationale', placeholder='Explain the evidence-to-need decision.')
            submitted = st.form_submit_button('Save review', type='primary', use_container_width=True)
        if submitted:
            result = api.post(f'/curation/evidence/{evidence_code}/review', {
                'decision': decision,
                'need_code': need_code.strip() or None,
                'reviewer': reviewer.strip(),
                'rationale': rationale.strip() or None,
            })
            st.success(f"Saved {result['decision']} decision for {result['reviewed']}.")
            st.rerun()

    with right:
        with st.container(border=True):
            st.markdown('#### Provenance')
            st.write(f"**Originating organization:** {evidence.get('originating_organization_name') or evidence.get('organization_name') or 'Unknown'}")
            st.write(f"**Year:** {evidence.get('event_year') or 'Unknown'}")
            st.write(f"**Source:** {evidence.get('source_title') or 'Unknown'}")
            st.write(f"**Section:** {evidence.get('source_section') or evidence.get('source_location') or 'Not recorded'}")
            st.write(f"**Page:** {evidence.get('source_page') or 'Not recorded'}")
            st.write(f"**Reviewed:** {'Yes' if evidence.get('human_reviewed') else 'No'}")

        if evidence.get('need_code'):
            with st.container(border=True):
                st.markdown('#### Linked canonical need')
                st.write(f"**{evidence['need_code']}**")
                st.write(evidence.get('canonical_need') or 'Canonical wording unavailable.')
                if st.button('Open linked need', use_container_width=True):
                    goto_need(evidence['need_code'])

    st.divider()
    evidence_link()
