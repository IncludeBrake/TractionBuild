import os, json
import psycopg
from datetime import datetime

DSN = os.getenv("DATABASE_URL")  # e.g. postgresql://user:pass@localhost:5432/tractionbuild

def _conn():
    if not DSN: return None
    return psycopg.connect(DSN, autocommit=True)

def create_project(p: dict):
    con = _conn(); 
    if not con: return
    with con.cursor() as cur:
        cur.execute("""
            insert into projects (id,name,description,state,metadata,results)
            values (%s,%s,%s,%s,%s::jsonb,%s::jsonb)
            on conflict (id) do update set
              name=excluded.name, description=excluded.description, state=excluded.state,
              metadata=excluded.metadata, results=excluded.results, updated_at=now()
        """, (p["id"], p["name"], p["description"], p["state"],
              json.dumps(p.get("metadata",{})), json.dumps(p.get("results",{}))))

def log_execution(project_id: str, agent: str, status: str, duration_ms: int, err: str|None=None):
    con = _conn(); 
    if not con: return
    with con.cursor() as cur:
        cur.execute("""
            insert into execution_logs (id, project_id, agent_name, tool_name, operation, status, duration_ms, error_message)
            values (gen_random_uuid(), %s, %s, %s, %s, %s, %s, %s)
        """, (project_id, agent, None, "execute", status, duration_ms, err))
