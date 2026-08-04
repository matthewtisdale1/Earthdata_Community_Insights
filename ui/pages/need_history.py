import json

import pandas as pd
import streamlit as st

import api_client as api
from styles import page_header


def render() -> None:
    page_header('Canonical Need Review History', 'Inspect the evidence breadth and audit trail for a canonical need.')
    needs = api.get('/needs', {'limit': 1000})
    options = {f"{item['need_code']} — {item['canonical_need']}": item['need_code'] for item in needs}
    if not options:
        st.info('No canonical needs are available.')
        return
    selected = st.selectbox('Canonical need', list(options))
    need_code = options[selected]

    summary = api.get(f'/curation/needs/{need_code}/evidence-summary')
    metrics = st.columns(5)
    metrics[0].metric('Evidence', summary.get('evidence_count', 0))
    metrics[1].metric('Sources', summary.get('source_count', 0))
    metrics[2].metric('Origins', summary.get('originating_organization_count', 0))
    metrics[3].metric('First seen', summary.get('first_seen_year') or '—')
    metrics[4].metric('Last seen', summary.get('last_seen_year') or '—')

    st.subheader('Canonical wording')
    st.write(summary['canonical_need'])
    st.subheader('Review history')
    history = api.get(f'/curation/needs/{need_code}/history')
    if not history:
        st.info('No review decisions have been recorded for this need.')
        return
    frame = pd.DataFrame(history)
    for column in ('previous_value', 'new_value'):
        if column in frame:
            frame[column] = frame[column].apply(
                lambda value: json.dumps(value, indent=2, default=str) if isinstance(value, (dict, list)) else value
            )
    st.dataframe(
        frame[['reviewed_at', 'decision_type', 'reviewer', 'review_notes', 'new_value']],
        hide_index=True,
        use_container_width=True,
        column_config={
            'reviewed_at': st.column_config.DatetimeColumn('Reviewed'),
            'decision_type': st.column_config.TextColumn('Decision'),
            'reviewer': st.column_config.TextColumn('Reviewer'),
            'review_notes': st.column_config.TextColumn('Rationale', width='large'),
            'new_value': st.column_config.TextColumn('Recorded change', width='large'),
        },
    )
