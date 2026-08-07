import json

import pandas as pd
import streamlit as st

import api_client as api
from styles import page_header


RELATIONSHIP_LABELS = {
    'Requires': 'Primary',
    'Supports': 'Secondary',
    'Related': 'Related',
}
LABEL_TO_RELATIONSHIP = {value: key for key, value in RELATIONSHIP_LABELS.items()}


def _set_index(value: int) -> None:
    st.session_state.knowledge_curation_index = value
    st.rerun()


def _curation_status(item: dict) -> str:
    return 'Curated' if item.get('human_reviewed') else 'Awaiting curation'


def render() -> None:
    page_header(
        'Knowledge Curation',
        'Curate canonical needs and the evidence and capability relationships that support them.',
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
    curation_status = filter_cols[2].selectbox(
        'Curation status',
        ['All', 'Awaiting curation', 'Curated'],
    )
    search = filter_cols[3].text_input('Search', placeholder='Need ID or wording')

    reviewed_filter = ''
    if curation_status == 'Curated':
        reviewed_filter = 'reviewed'
    elif curation_status == 'Awaiting curation':
        reviewed_filter = 'unreviewed'

    queue = api.get('/curation/review/needs', {
        'q': search,
        'organization': '' if organization == 'All' else organization,
        'community': '' if community == 'All' else community,
        'reviewed': reviewed_filter,
        'limit': 500,
    })
    if not queue:
        st.info('No knowledge records match the selected curation filters.')
        return

    curated_count = sum(bool(item.get('human_reviewed')) for item in queue)
    total = len(queue)
    remaining = total - curated_count
    progress_cols = st.columns([1, 1, 1, 3])
    progress_cols[0].metric('Records', total)
    progress_cols[1].metric('Curated', curated_count)
    progress_cols[2].metric('Remaining', remaining)
    with progress_cols[3]:
        st.caption('Curation progress')
        st.progress(curated_count / total if total else 1.0)
        st.caption(f'{curated_count / total * 100:.0f}% complete')

    codes = [item['need_code'] for item in queue]
    if 'knowledge_curation_index' not in st.session_state:
        st.session_state.knowledge_curation_index = 0
    index = min(st.session_state.knowledge_curation_index, len(codes) - 1)

    jump_labels = {
        f"{item['need_code']} — {item['canonical_need'][:95]}": idx
        for idx, item in enumerate(queue)
    }
    selected_label = st.selectbox(
        'Jump to knowledge record',
        list(jump_labels),
        index=index,
        key='knowledge_curation_jump',
    )
    selected_index = jump_labels[selected_label]
    if selected_index != index:
        st.session_state.knowledge_curation_index = selected_index
        index = selected_index

    need_code = codes[index]
    detail = api.get(f'/curation/review/needs/{need_code}')
    need = detail['need']
    evidence = detail.get('evidence') or []
    capabilities = detail.get('capabilities') or []
    origins = detail.get('origins') or []

    header = st.columns([4, 1, 1, 1, 1, 1])
    header[0].subheader(f"{need_code} · {need.get('need_category') or 'Uncategorized'}")
    header[1].metric('Quality', detail.get('quality_score', 100))
    header[2].metric('Evidence', len(evidence))
    header[3].metric('Capabilities', len(capabilities))
    header[4].metric('Organizations', need.get('organization_count') or 0)
    header[5].metric('Years', need.get('year_count') or 0)
    st.caption(f"Knowledge record {index + 1} of {total} · {_curation_status(need)}")

    canonical = st.text_area(
        'Canonical need',
        value=need.get('canonical_need') or '',
        height=110,
        key=f'curation_canonical_{need_code}',
    )
    desired_outcome = st.text_area(
        'Desired outcome',
        value=need.get('desired_outcome') or '',
        height=90,
        key=f'curation_outcome_{need_code}',
    )

    curator = st.text_input(
        'Curator',
        value=need.get('reviewer') or 'local-curator',
        key=f'curator_{need_code}',
    )
    curator_notes = st.text_area(
        'Curator notes',
        value=need.get('notes') or '',
        height=100,
        help='Capture durable interpretation, historical context, decisions, or follow-up questions.',
        key=f'curator_notes_{need_code}',
    )

    issues = detail.get('quality_issues') or []
    checklist = {
        'Canonical need': bool(canonical.strip()),
        'Desired outcome': bool(desired_outcome.strip()),
        'Supporting evidence': bool(evidence),
        'Capability mapping': bool(capabilities),
        'Curator identified': bool(curator.strip()),
        'Curation approved': bool(need.get('human_reviewed')),
    }
    with st.expander('Curation checklist', expanded=True):
        cols = st.columns(3)
        for position, (label, complete) in enumerate(checklist.items()):
            cols[position % 3].write(f"{'✓' if complete else '○'} {label}")

    with st.expander('Knowledge quality', expanded=bool(issues)):
        if not issues:
            st.success('No deterministic quality issues detected.')
        else:
            for issue in issues:
                st.warning(f"{issue['label']} · -{issue['penalty']} points")

    with st.expander('Supporting evidence', expanded=True):
        st.caption(
            'Evidence is immutable. Add and remove actions change only the curated relationship to this canonical need.'
        )
        evidence_note = st.text_input(
            'Evidence relationship rationale',
            placeholder='Optional reason for adding or removing an evidence relationship',
            key=f'evidence_note_{need_code}',
        )

        if not evidence:
            st.warning('No supporting evidence is linked to this need.')
        else:
            for record in evidence:
                text_col, action_col = st.columns([8, 1.4])
                with text_col:
                    title = ' · '.join(str(value) for value in (
                        record.get('event_year'),
                        record.get('originating_organization'),
                        record.get('source_title'),
                        record.get('evidence_code'),
                    ) if value)
                    st.markdown(f'**{title}**')
                    st.write(record.get('original_statement') or '—')
                    metadata = []
                    if record.get('user_community'):
                        metadata.append(f"Community: {record['user_community']}")
                    if record.get('source_location'):
                        metadata.append(f"Location: {record['source_location']}")
                    if record.get('link_review_status'):
                        metadata.append(f"Relationship: {record['link_review_status']}")
                    if record.get('link_reviewer'):
                        metadata.append(f"Curated by: {record['link_reviewer']}")
                    if metadata:
                        st.caption(' · '.join(metadata))
                with action_col:
                    if st.button(
                        'Remove',
                        key=f"curation_unlink_{need_code}_{record['evidence_code']}",
                        help='Remove only this evidence-to-need relationship.',
                        use_container_width=True,
                    ):
                        api.post(
                            f"/curation/review/needs/{need_code}/evidence/{record['evidence_code']}/unlink",
                            {
                                'reviewer': curator.strip() or 'local-curator',
                                'notes': evidence_note.strip() or None,
                            },
                        )
                        st.rerun()
                st.divider()

        st.markdown('#### Add evidence')
        evidence_search = st.text_input(
            'Find evidence',
            placeholder='Statement text, evidence ID, source, organization, or community',
            key=f'curation_evidence_search_{need_code}',
        )
        if len(evidence_search.strip()) >= 2:
            candidates = api.get('/curation/review/evidence/search', {
                'q': evidence_search.strip(),
                'need_code': need_code,
                'limit': 50,
            })
            if not candidates:
                st.info('No evidence matched that search.')
            for candidate in candidates:
                result_col, add_col = st.columns([8, 1.4])
                with result_col:
                    title = ' · '.join(str(value) for value in (
                        candidate.get('event_year'),
                        candidate.get('originating_organization'),
                        candidate.get('source_title'),
                        candidate.get('evidence_code'),
                    ) if value)
                    st.markdown(f'**{title}**')
                    st.write(candidate.get('original_statement') or '—')
                    metadata = []
                    if candidate.get('user_community'):
                        metadata.append(f"Community: {candidate['user_community']}")
                    if candidate.get('linked_need_codes'):
                        metadata.append(f"Currently linked: {candidate['linked_need_codes']}")
                    if metadata:
                        st.caption(' · '.join(metadata))
                with add_col:
                    if candidate.get('linked_to_current_need'):
                        st.success('Linked')
                    elif st.button(
                        'Add',
                        key=f"curation_link_{need_code}_{candidate['evidence_code']}",
                        use_container_width=True,
                    ):
                        api.post(
                            f"/curation/review/needs/{need_code}/evidence/{candidate['evidence_code']}/link",
                            {
                                'reviewer': curator.strip() or 'local-curator',
                                'notes': evidence_note.strip() or None,
                            },
                        )
                        st.rerun()
                st.divider()

    with st.expander('Capabilities', expanded=True):
        st.caption(
            'Curate the Earthdata capabilities needed to address this canonical need. Primary = core requirement; Secondary = supporting capability; Related = useful association.'
        )
        capability_note = st.text_input(
            'Capability relationship rationale',
            placeholder='Optional reason for adding, changing, or removing a capability',
            key=f'capability_note_{need_code}',
        )

        if not capabilities:
            st.warning('No capabilities are linked to this need.')
        else:
            for capability in capabilities:
                info_col, type_col, action_col = st.columns([5.5, 2, 1.4])
                with info_col:
                    st.markdown(f"**{capability['capability_name']}**")
                    st.caption(
                        ' · '.join(str(value) for value in (
                            capability.get('category'),
                            f"Status: {capability.get('review_status') or 'Pending'}",
                            f"Method: {capability.get('match_method') or '—'}",
                        ) if value)
                    )
                current_label = RELATIONSHIP_LABELS.get(capability.get('relationship_type'), 'Related')
                with type_col:
                    new_label = st.selectbox(
                        'Relationship',
                        ['Primary', 'Secondary', 'Related'],
                        index=['Primary', 'Secondary', 'Related'].index(current_label),
                        key=f"capability_type_{need_code}_{capability['capability_code']}",
                        label_visibility='collapsed',
                    )
                    if new_label != current_label:
                        if st.button(
                            'Update',
                            key=f"capability_update_{need_code}_{capability['capability_code']}",
                            use_container_width=True,
                        ):
                            api.post(
                                f"/curation/needs/{need_code}/capabilities/{capability['capability_code']}/link",
                                {
                                    'reviewer': curator.strip() or 'local-curator',
                                    'relationship_type': LABEL_TO_RELATIONSHIP[new_label],
                                    'confidence': capability.get('confidence'),
                                    'notes': capability_note.strip() or None,
                                },
                            )
                            st.rerun()
                with action_col:
                    if st.button(
                        'Remove',
                        key=f"capability_remove_{need_code}_{capability['capability_code']}",
                        use_container_width=True,
                    ):
                        api.post(
                            f"/curation/needs/{need_code}/capabilities/{capability['capability_code']}/unlink",
                            {
                                'reviewer': curator.strip() or 'local-curator',
                                'notes': capability_note.strip() or None,
                            },
                        )
                        st.rerun()
                st.divider()

        st.markdown('#### Add capability')
        capability_search = st.text_input(
            'Find capability',
            placeholder='Capability name, code, category, or description',
            key=f'capability_search_{need_code}',
        )
        capability_candidates = []
        if capability_search.strip():
            capability_candidates = api.get('/curation/capabilities/search', {
                'q': capability_search.strip(),
                'need_code': need_code,
                'limit': 50,
            })
        if capability_search.strip() and not capability_candidates:
            st.info('No capabilities matched that search.')
        for candidate in capability_candidates:
            info_col, type_col, add_col = st.columns([5.5, 2, 1.4])
            with info_col:
                st.markdown(f"**{candidate['capability_name']}**")
                st.caption(f"{candidate.get('category') or 'Uncategorized'} · {candidate.get('description') or ''}")
            with type_col:
                relationship_label = st.selectbox(
                    'Relationship',
                    ['Primary', 'Secondary', 'Related'],
                    key=f"candidate_type_{need_code}_{candidate['capability_code']}",
                    label_visibility='collapsed',
                )
            with add_col:
                if candidate.get('linked_to_current_need'):
                    st.success('Linked')
                elif st.button(
                    'Add',
                    key=f"capability_add_{need_code}_{candidate['capability_code']}",
                    use_container_width=True,
                ):
                    api.post(
                        f"/curation/needs/{need_code}/capabilities/{candidate['capability_code']}/link",
                        {
                            'reviewer': curator.strip() or 'local-curator',
                            'relationship_type': LABEL_TO_RELATIONSHIP[relationship_label],
                            'confidence': 1.0,
                            'notes': capability_note.strip() or None,
                        },
                    )
                    st.rerun()
            st.divider()

    with st.expander('Origin and time coverage', expanded=False):
        if origins:
            st.dataframe(pd.DataFrame(origins), hide_index=True, use_container_width=True)
        else:
            st.info('No originating organization information is linked.')

    with st.expander('Curation history', expanded=False):
        history = detail.get('history') or []
        if not history:
            st.info('No prior curation decisions have been recorded for this canonical need.')
        else:
            frame = pd.DataFrame(history)
            for column in ('previous_value', 'new_value'):
                if column in frame:
                    frame[column] = frame[column].apply(
                        lambda value: json.dumps(value, default=str) if isinstance(value, (dict, list)) else value
                    )
            columns = [c for c in ('reviewed_at', 'decision_type', 'reviewer', 'review_notes', 'new_value') if c in frame]
            st.dataframe(frame[columns], hide_index=True, use_container_width=True)

    st.info('Curator Assistant: reserved for future ChatGSFC integration. ECI does not generate or apply AI changes.')

    actions = st.columns([1, 1, 1, 1, 2])
    if actions[0].button('Previous', disabled=index == 0, use_container_width=True):
        _set_index(index - 1)

    if actions[1].button('Save', use_container_width=True):
        api.patch(f'/needs/{need_code}', {
            'canonical_need': canonical.strip(),
            'desired_outcome': desired_outcome.strip(),
            'reviewer': curator.strip() or 'local-curator',
            'notes': curator_notes.strip() or None,
        })
        st.success(f'Saved {need_code}.')

    if actions[2].button('Complete curation', type='primary', use_container_width=True):
        api.patch(f'/needs/{need_code}', {
            'canonical_need': canonical.strip(),
            'desired_outcome': desired_outcome.strip(),
            'human_reviewed': True,
            'reviewer': curator.strip() or 'local-curator',
            'notes': curator_notes.strip() or None,
        })
        if index < total - 1:
            _set_index(index + 1)
        else:
            st.success('Curation complete for the selected queue.')

    if actions[3].button('Next', disabled=index >= total - 1, use_container_width=True):
        _set_index(index + 1)

    actions[4].caption(
        'Complete curation records the human decision and advances automatically. Save preserves edits without changing curation status.'
    )
