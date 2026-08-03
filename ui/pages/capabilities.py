import pandas as pd
import streamlit as st

import api_client as api
from navigation import goto_capability
from styles import breadcrumb, page_header


def render() -> None:
    breadcrumb('Capabilities')
    page_header('Earthdata Capabilities', 'Explore what the Earthdata ecosystem can do and how community needs connect to tools and implementation evidence.')

    capabilities = api.get('/capabilities')
    if not capabilities:
        st.info('No capabilities are available. Apply migration 003 to create and seed the catalog.')
        return

    df = pd.DataFrame(capabilities)
    categories = ['All'] + sorted(df['category'].dropna().unique().tolist())
    selected = st.selectbox('Category', categories)
    query = st.text_input('Search capabilities', placeholder='Subsetting, search, visualization...')

    filtered = df.copy()
    if selected != 'All':
        filtered = filtered[filtered['category'] == selected]
    if query:
        mask = filtered['capability_name'].str.contains(query, case=False, na=False) | filtered['description'].str.contains(query, case=False, na=False)
        filtered = filtered[mask]

    for _, row in filtered.iterrows():
        with st.container(border=True):
            left, right = st.columns([5, 1.2])
            with left:
                st.markdown(f"### {row['capability_name']}")
                st.caption(f"{row.get('category') or 'Uncategorized'} · {row.get('maturity') or 'Unknown maturity'}")
                st.write(row.get('description') or '')
                metrics = st.columns(4)
                metrics[0].metric('Needs', int(row.get('need_count') or 0))
                metrics[1].metric('Evidence', int(row.get('evidence_count') or 0))
                metrics[2].metric('Organizations', int(row.get('organization_count') or 0))
                metrics[3].metric('Tools', int(row.get('tool_count') or 0))
            with right:
                if st.button('Open', key=f"open_cap_{row['capability_code']}", use_container_width=True):
                    goto_capability(row['capability_code'])
