import streamlit as st

import api_client as api
from navigation import goto_need
from styles import page_header


ISSUE_OPTIONS = {
    'All issues': '',
    'Missing desired outcome': 'missing_outcome',
    'Missing capability': 'missing_capability',
    'Not human reviewed': 'not_reviewed',
    'Implementation language': 'implementation_language',
    'Possible multiple outcomes': 'multiple_outcomes',
    'Low evidence': 'low_evidence',
    'Nonstandard canonical format': 'canonical_format',
    'Long statement': 'long_statement',
    'Missing punctuation': 'punctuation',
}


def render() -> None:
    page_header(
        'Knowledge Quality',
        'Measure corpus health and identify canonical needs that require human attention.',
    )

    summary = api.get('/curation/quality/summary')
    corpus = summary.get('corpus') or {}

    metrics = st.columns(5)
    metrics[0].metric('Overall health', f"{summary.get('overall_health', 100):.1f}%")
    metrics[1].metric('Needs attention', summary.get('needs_attention', 0))
    metrics[2].metric('Human reviewed', f"{summary.get('reviewed_percent', 0):.1f}%")
    metrics[3].metric('Canonical needs', corpus.get('need_count', summary.get('total_needs', 0)))
    metrics[4].metric('Evidence records', corpus.get('evidence_count', 0))

    with st.expander('Corpus coverage', expanded=False):
        coverage = st.columns(4)
        coverage[0].metric('Communities', corpus.get('community_count', 0))
        coverage[1].metric('Organizations', corpus.get('organization_count', 0))
        coverage[2].metric('First year', corpus.get('first_year') or '—')
        coverage[3].metric('Last year', corpus.get('last_year') or '—')

    issue_counts = summary.get('issue_counts') or {}
    st.subheader('Quality issues')
    issue_metrics = st.columns(4)
    issue_metrics[0].metric('Missing outcome', issue_counts.get('missing_outcome', 0))
    issue_metrics[1].metric('Missing capability', issue_counts.get('missing_capability', 0))
    issue_metrics[2].metric('Implementation language', issue_counts.get('implementation_language', 0))
    issue_metrics[3].metric('Low evidence', issue_counts.get('low_evidence', 0))

    search_col, issue_col, score_col = st.columns([2, 1.4, 1])
    search = search_col.text_input('Search needs', placeholder='Search need ID or wording')
    issue_label = issue_col.selectbox('Issue type', list(ISSUE_OPTIONS))
    max_score_label = score_col.selectbox('Quality score', ['All', '< 90', '< 80', '< 70'])
    max_score = {'All': None, '< 90': 89, '< 80': 79, '< 70': 69}[max_score_label]

    params = {
        'q': search,
        'issue': ISSUE_OPTIONS[issue_label],
        'limit': 500,
    }
    if max_score is not None:
        params['max_score'] = max_score

    needs = api.get('/curation/quality/needs', params)
    needs = [item for item in needs if item.get('issue_count', 0) > 0]
    st.caption(f"{len(needs)} needs require attention. Scores are deterministic and explainable; no text is rewritten automatically.")

    if not needs:
        st.success('No needs matched the selected quality filters.')
        return

    for item in needs:
        issues = item.get('quality_issues') or []
        with st.container(border=True):
            heading, score_col, action_col = st.columns([6, 1.1, 1.2])
            with heading:
                st.markdown(f"### {item['need_code']}")
                st.write(item['canonical_need'])
                st.caption(
                    f"{item.get('evidence_count', 0)} evidence records · "
                    f"{item.get('organization_count', 0)} originating organizations · "
                    f"{item.get('year_count', 0)} years represented"
                )
            with score_col:
                st.metric('Quality', item.get('quality_score', 0))
            with action_col:
                if st.button('Review need', key=f"review_{item['need_code']}", use_container_width=True):
                    goto_need(item['need_code'])

            for issue in issues:
                st.warning(f"{issue['label']}  (−{issue['penalty']})", icon='⚠️')

            checks = []
            if item.get('human_reviewed'):
                checks.append('Human reviewed')
            if item.get('desired_outcome'):
                checks.append('Desired outcome recorded')
            if int(item.get('capability_count') or 0) > 0:
                checks.append('Capability mapped')
            if int(item.get('evidence_count') or 0) > 1:
                checks.append('Multiple supporting evidence records')
            if checks:
                st.caption('✓ ' + ' · ✓ '.join(checks))
