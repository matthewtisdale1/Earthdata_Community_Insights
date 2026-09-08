from datetime import date
import requests
import streamlit as st
from api_client import get, post, API_BASE_URL
from navigation import goto_need

STATUSES=['Backlog','Planned','In progress','Blocked','Delivered','Cancelled']

def render():
    st.title('PI Planning & Outcomes')
    st.caption('Connect community needs to delivery commitments and reviewed outcomes.')
    try:
        data=get('/planning')
    except requests.RequestException:
        st.error('Planning is unavailable. Apply the planning migration using scripts/enable-planning.ps1, then reload.')
        return
    reviewer=st.text_input('Your name',key='planning_reviewer')
    st.caption('Local prototype: names record attribution; sign-in is not yet enforced.')
    board, setup, outcome=st.tabs(['Deliverables','Teams & PIs','Need outcomes'])
    with setup:
        with st.form('team'):
            name=st.text_input('Team name')
            kind=st.selectbox('Team type',['ASSET','DAAC','Enterprise','Other'])
            if st.form_submit_button('Add team'):
                submit('/planning/teams',dict(name=name,kind=kind))
        st.dataframe(data['teams'],hide_index=True)
        with st.form('pi'):
            name=st.text_input('PI name')
            starts=st.date_input('Start date',date.today())
            ends=st.date_input('End date',date.today())
            if st.form_submit_button('Add PI'):
                submit('/planning/pis',dict(name=name,starts=str(starts),ends=str(ends)))
        st.dataframe(data['pis'],hide_index=True)
    with board:
        teams={None:'Unassigned',**{r['id']:r['name'] for r in data['teams']}}
        pis={None:'Unscheduled',**{r['id']:r['name'] for r in data['pis']}}
        a,b,c=st.columns(3)
        team=a.selectbox('Filter team',['All']+list(teams.values()))
        pi=b.selectbox('Filter PI',['All']+list(pis.values()))
        status=c.selectbox('Filter status',['All']+STATUSES)
        rows=[r for r in data['work'] if (team=='All' or teams[r['team_id']]==team)
              and (pi=='All' or pis[r['pi_id']]==pi) and (status=='All' or r['status']==status)]
        st.metric('Deliverables in view',len(rows))
        if rows:
            st.dataframe([{k:r[k] for k in ['id','need_code','title','team_name','pi_name','status']} for r in rows],hide_index=True,use_container_width=True)
        else: st.info('No deliverables in this view. Add one below using an existing need code.')
        selected=st.selectbox('Create or edit',[None]+[r['id'] for r in rows],format_func=lambda x:'New deliverable' if x is None else f'Deliverable {x}')
        item=next((r for r in rows if r['id']==selected),{})
        with st.form(f'work_{selected}'):
            code=st.text_input('Need code',item.get('need_code',''),disabled=selected is not None)
            title=st.text_input('Deliverable',item.get('title',''))
            acceptance=st.text_area('Acceptance criteria',item.get('acceptance',''))
            team_id=st.selectbox('Owner team',list(teams),index=list(teams).index(item.get('team_id')),format_func=teams.get)
            pi_id=st.selectbox('Target PI',list(pis),index=list(pis).index(item.get('pi_id')),format_func=pis.get)
            state=st.selectbox('Delivery status',STATUSES,index=STATUSES.index(item.get('status','Backlog')))
            link=st.text_input('Jira / GitHub / delivery reference',item.get('delivery_link',''))
            evidence=st.text_area('Completion evidence',item.get('evidence',''),help='Describe what was delivered and how acceptance was verified. Required for Delivered.')
            reason=st.text_input('Reason for this change')
            if st.form_submit_button('Save deliverable'):
                payload=dict(need_code=code,title=title,acceptance=acceptance,team_id=team_id,pi_id=pi_id,status=state,delivery_link=link,evidence=evidence,reviewer=reviewer,reason=reason,version=item.get('version',1))
                submit('/planning/work' if selected is None else f'/planning/work/{selected}',payload,put=selected is not None)
        if selected:
            if st.button('Open source need and evidence'): goto_need(item['need_code'])
            st.subheader('Change history')
            st.json(get(f'/planning/history/{selected}'))
    with outcome:
        st.write('Delivery completion does not automatically satisfy a user need. Record the reviewed outcome and supporting evidence here.')
        with st.form('outcome'):
            code=st.text_input('Need code to assess')
            state=st.selectbox('Outcome',['Unassessed','Unmet','Partially met','Satisfied','Superseded'])
            evidence=st.text_area('Outcome evidence and rationale')
            if st.form_submit_button('Record assessment'):
                submit(f'/planning/outcomes/{code}',dict(status=state,evidence=evidence,reviewer=reviewer))
        latest={}
        for r in data['outcomes']: latest.setdefault(r['need_code'],r)
        st.subheader('Latest assessments')
        st.dataframe(list(latest.values()),hide_index=True)
        with st.expander('All assessment history'): st.dataframe(data['outcomes'],hide_index=True)

def submit(path,payload,put=False):
    try:
        if put:
            response=requests.put(API_BASE_URL+path,json=payload,timeout=30)
            response.raise_for_status()
        else: post(path,payload)
    except requests.RequestException as exc:
        response=getattr(exc,'response',None)
        st.error(response.text if response is not None else str(exc))
        return
    st.rerun()
