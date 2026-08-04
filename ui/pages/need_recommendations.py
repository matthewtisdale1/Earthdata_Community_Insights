import streamlit as st

import api_client as api
from navigation import goto_need
from styles import page_header


ISSUE_OPTIONS = [
    'All issues',
    'Grammar or canonical-prefix correction',
    'canonical Earthdata-wide need format',
    'implementation- or organization-specific language',
    'multiple outcomes',
    'terminal punctuation',
]


def render() -> None:
    page_header(
        'Need Recommendations',
        'Review suggested canonical wording improvements before applying them.',
    )

    summary = api.get('/curation/needs/recommendations/summary')
    metrics = st.columns(5)
    metrics[0].metric('Total needs', summary.get('total_needs', 0))
    metrics[1].metric('Flagged', summary.get('flagged_needs', 0))
    metrics[2].metric('Grammar / format', summary.get('grammar_or_format', 0))
    metrics[3].metric('Implementation language', summary.get('implementation_language', 0))
    metrics[4].metric('Possible multi-outcome', summary.get('possible_multiple_outcomes', 0))

    search_col, issue_col = st.columns([2, 1])
    search = search_col.text_input(
        'Search needs',
        placeholder='Search need ID or wording',
    )
    issue_label = issue_col.selectbox('Issue type', ISSUE_OPTIONS)
    issue = '' if issue_label == 'All issues' else issue_label

    recommendations = api.get(
        '/curation/needs/recommendations',
        {'q': search, 'issue': issue, 'limit': 500},
    )
    st.caption(f"{len(recommendations)} needs require review. Suggestions are deterministic review aids, not automatic decisions.")

    if not recommendations:
        st.success('No needs matched the selected recommendation filters.')
        return

    for item in recommendations:
        need_code = item['need_code']
        reasons = item.get('recommendation_reasons') or []
        with st.expander(
            f"{need_code} · {len(reasons)} issue{'s' if len(reasons) != 1 else ''}",
            expanded=False,
        ):
            context = st.columns(4)
            context[0].metric('Evidence', item.get('evidence_count', 0))
            context[1].metric('Organizations', item.get('organization_count', 0))
            context[2].metric('Years', item.get('year_count', 0))
            context[3].write(f"**Status:** {item.get('lifecycle_status') or 'Candidate'}")

            st.markdown('**Why it was flagged**')
            for reason in reasons:
                st.write(f'- {reason}')

            left, right = st.columns(2, gap='large')
            with left:
                st.markdown('#### Current canonical need')
                st.info(item['canonical_need'])
            with right:
                st.markdown('#### Recommended canonical need')
                proposed = st.text_area(
                    'Edit recommendation before approval',
                    value=item['recommended_canonical_need'],
                    height=150,
                    key=f'recommendation_{need_code}',
                    label_visibility='collapsed',
                )

            reviewer = st.text_input(
                'Reviewer',
                value='local-reviewer',
                key=f'reviewer_{need_code}',
            )
            notes = st.text_area(
                'Review rationale',
                value='; '.join(reasons),
                key=f'notes_{need_code}',
            )

            apply_col, open_col = st.columns([1, 1])
            if apply_col.button(
                'Approve and apply wording',
                key=f'apply_{need_code}',
                type='primary',
                use_container_width=True,
            ):
                if not proposed.strip().lower().startswith('earthdata users need'):
                    st.error('Approved canonical needs must begin with “Earthdata users need”.')
                elif not reviewer.strip():
                    st.error('A reviewer is required.')
                else:
                    api.patch(
                        f'/needs/{need_code}',
                        {
                            'canonical_need': proposed.strip(),
                            'human_reviewed': True,
                            'reviewer': reviewer.strip(),
                            'notes': notes.strip() or None,
                        },
                    )
                    st.success(f'Updated {need_code}.')
                    st.rerun()

            if open_col.button(
                'Open complete need record',
                key=f'open_{need_code}',
                use_container_width=True,
            ):
                goto_need(need_code)
