"""Local prototype planning. Reviewer names are attributed, not authenticated."""
import json
from datetime import date
from typing import Literal
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import text
from app.main_quality import app, engine

class Input(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')

class Team(Input):
    name: str = Field(min_length=1, max_length=200)
    kind: Literal['ASSET', 'DAAC', 'Enterprise', 'Other'] = 'ASSET'

class PI(Input):
    name: str = Field(min_length=1, max_length=100)
    starts: date
    ends: date

    @model_validator(mode='after')
    def dates(self):
        if self.ends < self.starts:
            raise ValueError('End must be on or after start')
        return self

class Work(Input):
    need_code: str = Field(min_length=1, max_length=40)
    title: str = Field(min_length=1, max_length=500)
    acceptance: str = Field(min_length=1, max_length=10000)
    team_id: int | None = None
    pi_id: int | None = None
    status: Literal['Backlog', 'Planned', 'In progress', 'Blocked', 'Delivered', 'Cancelled'] = 'Backlog'
    delivery_link: str = Field(default='', max_length=2000)
    evidence: str = Field(default='', max_length=10000)
    reviewer: str = Field(min_length=1, max_length=200)
    reason: str = Field(min_length=1, max_length=10000)
    version: int = Field(default=1, ge=1)

    @model_validator(mode='after')
    def complete(self):
        if self.status == 'Delivered' and not self.evidence:
            raise ValueError('Delivered work requires completion evidence')
        if self.status in ('Planned', 'In progress', 'Blocked', 'Delivered') and (self.pi_id is None or self.team_id is None):
            raise ValueError('Scheduled work requires a PI and owner team')
        return self

class Outcome(Input):
    status: Literal['Unassessed', 'Unmet', 'Partially met', 'Satisfied', 'Superseded']
    evidence: str = Field(min_length=1, max_length=10000)
    reviewer: str = Field(min_length=1, max_length=200)


def audit(c, kind, key, before, after, reviewer, reason):
    c.execute(text('''INSERT INTO planning_history(entity_type, entity_key, previous_value,
        new_value, reviewer, reason) VALUES (:kind,:key,:before,:after,:reviewer,:reason)'''),
        dict(kind=kind, key=str(key), before=json.dumps(before, default=str),
             after=json.dumps(after, default=str), reviewer=reviewer, reason=reason))

@app.get('/planning')
def planning():
    with engine.connect() as c:
        def rows(sql): return [dict(r) for r in c.execute(text(sql)).mappings()]
        return dict(teams=rows('SELECT * FROM planning_teams ORDER BY name'),
                    pis=rows('SELECT * FROM planning_pis ORDER BY starts DESC'),
                    work=rows('''SELECT w.*, n.need_code, n.canonical_need, t.name AS team_name,
                        p.name AS pi_name FROM planning_work w JOIN needs n ON n.need_id=w.need_id
                        LEFT JOIN planning_teams t ON t.id=w.team_id
                        LEFT JOIN planning_pis p ON p.id=w.pi_id ORDER BY w.id DESC'''),
                    outcomes=rows('''SELECT o.*, n.need_code FROM planning_outcomes o
                        JOIN needs n ON n.need_id=o.need_id ORDER BY o.id DESC'''))

@app.post('/planning/teams', status_code=201)
def create_team(value: Team):
    with engine.begin() as c:
        if c.execute(text('SELECT id FROM planning_teams WHERE name=:name'), value.model_dump()).first():
            raise HTTPException(409, 'Team already exists')
        r=c.execute(text('INSERT INTO planning_teams(name,kind) VALUES (:name,:kind)'), value.model_dump())
        return {'id': r.lastrowid}

@app.post('/planning/pis', status_code=201)
def create_pi(value: PI):
    with engine.begin() as c:
        if c.execute(text('SELECT id FROM planning_pis WHERE name=:name'), value.model_dump()).first():
            raise HTTPException(409, 'PI already exists')
        r=c.execute(text('INSERT INTO planning_pis(name,starts,ends) VALUES (:name,:starts,:ends)'), value.model_dump())
        return {'id': r.lastrowid}


def save_work(value, work_id=None):
    data=value.model_dump()
    with engine.begin() as c:
        need=c.execute(text('SELECT need_id FROM needs WHERE need_code=:need_code'), data).scalar()
        if need is None: raise HTTPException(404, 'Need not found')
        data['need_id']=need
        for key, table in [('team_id','planning_teams'),('pi_id','planning_pis')]:
            if data[key] is not None and not c.execute(text(f'SELECT id FROM {table} WHERE id=:id'), {'id':data[key]}).first():
                raise HTTPException(404, f'{key} not found')
        before=None
        if work_id is None:
            data['version']=1
            r=c.execute(text('''INSERT INTO planning_work(need_id,title,acceptance,team_id,pi_id,status,
                delivery_link,evidence,version) VALUES (:need_id,:title,:acceptance,:team_id,:pi_id,:status,
                :delivery_link,:evidence,1)'''), data)
            work_id=r.lastrowid
        else:
            before=c.execute(text('SELECT * FROM planning_work WHERE id=:id'), {'id':work_id}).mappings().first()
            if not before: raise HTTPException(404, 'Deliverable not found')
            before=dict(before)
            if before['need_id'] != need: raise HTTPException(422, 'A deliverable cannot be moved to another need')
            data['id']=work_id
            r=c.execute(text('''UPDATE planning_work SET title=:title, acceptance=:acceptance,
                team_id=:team_id,pi_id=:pi_id,status=:status,delivery_link=:delivery_link,
                evidence=:evidence,version=version+1 WHERE id=:id AND version=:version'''), data)
            if r.rowcount != 1: raise HTTPException(409, 'This record changed. Reload before saving.')
            data['version']+=1
        audit(c,'Deliverable',work_id,before,data,value.reviewer,value.reason)
        return {'id': work_id, 'version': data['version']}

@app.post('/planning/work', status_code=201)
def create_work(value: Work): return save_work(value)

@app.put('/planning/work/{work_id}')
def update_work(work_id: int, value: Work): return save_work(value,work_id)

@app.post('/planning/outcomes/{need_code}', status_code=201)
def assess_outcome(need_code: str, value: Outcome):
    with engine.begin() as c:
        need=c.execute(text('SELECT need_id FROM needs WHERE need_code=:code'), {'code':need_code}).scalar()
        if need is None: raise HTTPException(404,'Need not found')
        data=value.model_dump();data['need_id']=need
        c.execute(text('''INSERT INTO planning_outcomes(need_id,status,evidence,reviewer)
            VALUES (:need_id,:status,:evidence,:reviewer)'''),data)
    return {'assessed':need_code}

@app.get('/planning/history/{work_id}')
def history(work_id: int):
    with engine.connect() as c:
        return [dict(r) for r in c.execute(text("SELECT * FROM planning_history WHERE entity_type='Deliverable' AND entity_key=:key ORDER BY id DESC"),{'key':str(work_id)}).mappings()]
