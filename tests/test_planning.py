import os
os.environ['DATABASE_URL']='mysql+pymysql://test:test@localhost/test'
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool
from app import main_planning as planning

engine=create_engine('sqlite://',connect_args={'check_same_thread':False},poolclass=StaticPool)
planning.engine=engine
with engine.begin() as c:
    for sql in [
        'CREATE TABLE needs(need_id INTEGER PRIMARY KEY, need_code TEXT, canonical_need TEXT)',
        "INSERT INTO needs VALUES (1,'NEED-TEST','Users need useful guidance')",
        'CREATE TABLE planning_teams(id INTEGER PRIMARY KEY,name TEXT,kind TEXT)',
        'CREATE TABLE planning_pis(id INTEGER PRIMARY KEY,name TEXT,starts DATE,ends DATE)',
        'CREATE TABLE planning_work(id INTEGER PRIMARY KEY,need_id INTEGER,title TEXT,acceptance TEXT,team_id INTEGER,pi_id INTEGER,status TEXT,delivery_link TEXT,evidence TEXT,version INTEGER)',
        'CREATE TABLE planning_history(id INTEGER PRIMARY KEY,entity_type TEXT,entity_key TEXT,previous_value TEXT,new_value TEXT,reviewer TEXT,reason TEXT)',
        'CREATE TABLE planning_outcomes(id INTEGER PRIMARY KEY,need_id INTEGER,status TEXT,evidence TEXT,reviewer TEXT)',
    ]: c.execute(text(sql))
client=TestClient(planning.app)

def test_delivery_review_and_transition_history():
    t=client.post('/planning/teams',json={'name':'Legacy DAAC','kind':'DAAC'}).json()['id']
    t2=client.post('/planning/teams',json={'name':'Future team','kind':'ASSET'}).json()['id']
    assert client.post('/planning/pis',json={'name':'Bad','starts':'2026-12-01','ends':'2026-01-01'}).status_code==422
    pi=client.post('/planning/pis',json={'name':'PI test','starts':'2026-10-01','ends':'2026-12-31'}).json()['id']
    payload=dict(need_code='NEED-TEST',title='Publish tutorial',acceptance='Tutorial tested with users',team_id=t,pi_id=pi,status='Planned',reviewer='Tester',reason='Initial commitment')
    r=client.post('/planning/work',json=payload)
    assert r.status_code==201,r.text
    wid=r.json()['id']
    assert client.put(f'/planning/work/{wid}',json={**payload,'status':'Delivered'}).status_code==422
    assert client.post('/planning/work',json={**payload,'team_id':999}).status_code==404
    payload.update(team_id=t2,reason='ASSET handover',version=1)
    assert client.put(f'/planning/work/{wid}',json=payload).status_code==200
    assert client.put(f'/planning/work/{wid}',json=payload).status_code==409
    history=client.get(f'/planning/history/{wid}').json()
    assert len(history)==2
    import json
    assert json.loads(history[0]['previous_value'])['team_id']==t
    assert json.loads(history[0]['new_value'])['team_id']==t2
    payload.update(version=2,status='Delivered',evidence='Tutorial URL and user acceptance recorded',reason='Acceptance checked')
    assert client.put(f'/planning/work/{wid}',json=payload).status_code==200
    assert client.get('/planning').json()['outcomes']==[]
    for state in ['Partially met','Satisfied']:
        assert client.post('/planning/outcomes/NEED-TEST',json={'status':state,'reviewer':'Tester','evidence':'Reviewed user outcome'}).status_code==201
    assert len(client.get('/planning').json()['outcomes'])==2
