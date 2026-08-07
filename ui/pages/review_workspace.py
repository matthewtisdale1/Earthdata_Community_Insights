import json

import pandas as pd
import streamlit as st

import api_client as api
from styles import page_header


def _set_index(value: int) -> None:
    st.session_state.review_workspace_index = value
    st.rerun()


def render() -> None:
    page_header(
        'Knowledge Review Workspace',
        'Review canonical needs, supporting evidence, capabilities, quality issues, and history in one place.',
    )

    options = api.get('/curation/review/options')
    filter_cols = st.columns([1.4, 1.4, 1, 1.5])
    organization = filter_cols[0].selectbox(
        'Originating organization',
        ['All'] + (options.get('organizations') or []),
    )
    community = filter_cols[1].selectbox(
        'User community',
        ['All'] + (options.get('communities') or []),
    )
    review_status = filter_cols[2].selectbox(
        'Review status',
        ['All', 'Unreviewed', 'Reviewed'],
    )
    search = filter_cols[3].text_input('Search', placeholder='Need ID or wording')

    params = {
        'q': search,
        'organization': '' if organization == 'All' else organization,
        'community': '' if community == 'All' else community,
        'reviewed': '' if review_status == 'All' else review_status.lower(),
        'limit': 500,
    }
    queue = api.get('/curation/review/needs', params)
    if not queue:
        st.info('No canonical needs match the selected review filters.')
        return

    reviewed_count = sum(bool(item.get('human_reviewed')) for item in queue)
    total = len(queue)
    remaining = total - reviewed_count
    progress_cols = st.columns([1, 1, 1, 3])
    progress_cols[0].metric('Needs', total)
    progress_cols[1].metric('Reviewed', reviewed_count)
    progress_cols[2].metric('Remaining', remaining)
    with progress_cols[3]:
        st.caption('Review progress')
        st.progress(reviewed_count / total if total else 1.0)
        st.caption(f'{reviewed_count / total * 100:.0f}% complete')

    codes = [item['need_code'] for item in queue]
    if 'review_workspace_index' not in st.session_state:
        st.session_state.review_workspace_index = 0
    index = min(st.session_state.review_workspace_index, len(codes) - 1)

    jump_labels = {
        f"{item['need_code']} — {item['canonical_need'][:95]}": idx
        for idx, item in enumerate(queue)
    }
    selected_label = st.selectbox(
        'Jump to canonical need',
        list(jump_labels),
        index=index,
        key='review_workspace_jump',
    )
    selected_index = jump_labels[selected_label]
    if selected_index != index:
        st.session_state.review_workspace_index = selected_index
        index = selected_index

    need_code = codes[index]
    detail = api.get(f'/curation/review/needs/{need_code}')
    need = detail['need']

    header_cols = st.columns([5, 1, 1])
    header_cols[0].subheader(f"{need_code} · {need.get('need_category') or 'Uncategorized'}")
    header_cols[1].metric('Quality', detail.get('quality_score', 100))
    header_cols[2].metric('Evidence', len(detail.get('evidence') or []))
    st.caption(f'Need {index + 1} of {total}')

    canonical = st.text_area(
        'Canonical need',
        value=need.get('canonical_need') or '',
        height=110,
        key=f'canonical_{need_code}',
    )
    desired_outcome = st.text_area(
        'Desired outcome',
        value=need.get('desired_outcome') or '',
        height=90,
        key=f'outcome_{need_code}',
    )

    meta = st.columns(4)
    meta[0].write(f"**Status:** {need.get('lifecycle_status') or 'Candidate'}")
    meta[1].write(f"**Reviewer:** {need.get('reviewer') or '—'}")
    meta[2].write(f"**Organizations:** {need.get('organization_count') or 0}")
    meta[3].write(f"**Years:** {need.get('year_count') or 0}")

    with st.expander('Quality issues', expanded=bool(detail.get('quality_issues'))):
        issues = detail.get('quality_issues') or []
        if not issues:
            st.success('No deterministic quality issues detected.')
        else:
            for issue in issues:
                st.warning(f"{issue['label']}  ·  -{issue['penalty']} points")

    with st.expander('Capabilities', expanded=True):
        capabilities = detail.get('capabilities') or []
        if not capabilities:
            st.warning('No capability mappings are linked to this need.')
        else:
            st.dataframe(
                pd.DataFrame(capabilities)[[
                    'capability_name', 'category', 'relationship_type',
                    'confidence', 'review_status', 'match_method'
                ]],
                hide_index=True,
                use_container_width=True,
            )

    with st.expander('Origin and time coverage', expanded=False):
        origins = detail.get('origins') or []
        if origins:
            st.dataframe(pd.DataFrame(origins), hide_index=True, use_container_width=True)
        else:
            st.info('No originating organization information is linked.')

    with st.expander('Supporting evidence', expanded=True):
        evidence = detail.get('evidence') or []
        if not evidence:
            st.warning('No supporting evidence is linked to this need.')
        else:
            for record in evidence:
                title = ' · '.join(
                    str(value) for value in (
                        record.get('event_year'),
                        record.get('originating_organization'),
                        record.get('source_title'),
                        record.get('evidence_code'),
                    ) if value
                )
                st.markdown(f'**{title}**')
                st.write(record.get('original_statement') or '—')
                details = []
                if record.get('user_community'):
                    details.append(f"Community: {record['user_community']}")
                if record.get('source_location'):
                    details.append(f"Location: {record['source_location']}")
                if details:
                    st.caption(' · '.join(details))
                st.divider()

    reviewer_notes = st.text_area(
        'Reviewer notes',
        value=need.get('notes') or '',
        height=100,
        help='Capture durable context or rationale. Avoid notes that only say “looks good.”',
        key=f'notes_{need_code}',
    )
    reviewer = st.text_input(
        'Reviewer',
        value=need.get('reviewer') or 'local-reviewer',
        key=f'reviewer_{need_code}',
    )

    with st.expander('Previous reviews', expanded=False):
        history = detail.get('history') or []
        if not history:
            st.info('No prior review decisions have been recorded.')
        else:
            frame = pd.DataFrame(history)
            for column in ('previous_value', 'new_value'):
                if column in frame:
                    frame[column] = frame[column].apply(
                        lambda value: json.dumps(value, default=str) if isinstance(value, (dict, list)) else value
                    )
            columns = [c for c in ('reviewed_at', 'decision_type', 'reviewer', 'review_notes', 'new_value') if c in frame]
            st.dataframe(frame[columns], hide_index=True, use_container_width=True)

    st.info('AI Review Assistant: reserved for future ChatGSFC integration. No AI-generated changes are applied by ECI.')

    action_cols = st.columns([1, 1, 1, 1, 2])
    if action_cols[0].button('Previous', disabled=index == 0, use_container_width=True):
        _set_index(index - 1)

    if action_cols[1].button('Save', use_container_width=True):
        api.patch(
            f'/needs/{need_code}',
            {
                'canonical_need': canonical.strip(),
                'desired_outcome': desired_outcome.strip(),
                'reviewer': reviewer.strip() or 'local-reviewer',
                'notes': reviewer_notes.strip() or None,
            },
        )
        st.success(f'Saved {need_code}.')

    if action_cols[2].button('Approve', type='primary', use_container_width=True):
        api.patch(
            f'/needs/{need_code}',
            {
                'canonical_need': canonical.strip(),
                'desired_outcome': desired_outcome.strip(),
                'human_reviewed': True,
                'reviewer': reviewer.strip() or 'local-reviewer',
                'notes': reviewer_notes.strip() or None,
            },
        )
        if index < total - 1:
            _set_index(index + 1)
        else:
            st.success('Review complete for the selected queue.')

    if action_cols[3].button('Next', disabled=index >= total - 1, use_container_width=True):
        _set_index(index + 1)

    action_cols[4].caption(
        'Approve records the review and advances automatically. Save preserves edits without changing review status.'
    )
