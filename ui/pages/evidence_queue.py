import pandas as pd
import streamlit as st

import api_client as api
from navigation import goto_evidence
from styles import page_header


def render() -> None:
    page_header('Evidence Review Queue', 'Review community evidence before publishing curated knowledge.')

    summary = api.get('/curation/evidence/summary')
    cols = st.columns(4)
    cols[0].metric('Unreviewed', int(summary.get('unreviewed') or 0))
    cols[1].metric('Reviewed', int(summary.get('reviewed') or 0))
    cols[2].metric('Sources', int(summary.get('source_count') or 0))
    cols[3].metric('Years', int(summary.get('year_count') or 0))

    search_col, status_col, year_col = st.columns([3, 1, 1])
    search = search_col.text_input('Search', placeholder='Evidence, need, or identifier')
    status = status_col.selectbox('Status', ['Unreviewed', 'All', 'Reviewed'])
    year_text = year_col.text_input('Year', placeholder='2024')

    params = {'q': search, 'limit': 1000}
    if status != 'All':
        params['reviewed'] = status == 'Reviewed'
    if year_text.strip().isdigit():
        params['year'] = int(year_text)

    records = api.get('/curation/evidence', params)
    st.caption(f'{len(records)} records in the current queue')
    if not records:
        st.info('No evidence matched the selected filters.')
        return

    frame = pd.DataFrame(records)
    columns = [
        'evidence_code', 'original_statement', 'originating_organization',
        'event_year', 'source_title', 'review_status', 'need_code'
    ]
    event = st.dataframe(
        frame[columns], hide_index=True, use_container_width=True, height=650,
        selection_mode='single-row', on_select='rerun',
        column_config={
            'evidence_code': st.column_config.TextColumn('Evidence ID', width='small'),
            'original_statement': st.column_config.TextColumn('Original Evidence', width='large'),
            'originating_organization': st.column_config.TextColumn('Origin', width='medium'),
            'event_year': st.column_config.NumberColumn('Year', format='%d'),
            'source_title': st.column_config.TextColumn('Source', width='medium'),
            'review_status': st.column_config.TextColumn('Status', width='small'),
            'need_code': st.column_config.TextColumn('Need', width='small'),
        },
    )
    if event.selection.rows:
        goto_evidence(records[event.selection.rows[0]]['evidence_code'])
