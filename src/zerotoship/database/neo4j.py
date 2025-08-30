import os
from neo4j import GraphDatabase

URI = os.getenv("NEO4J_URI")              # bolt://localhost:7687 or neo4j://...
USER = os.getenv("NEO4J_USER","neo4j")
PWD  = os.getenv("NEO4J_PASSWORD","password")

_driver = None
def driver():
    global _driver
    if not (URI and USER and PWD): return None
    if _driver is None:
        _driver = GraphDatabase.driver(URI, auth=(USER,PWD))
    return _driver

def upsert_project(project_id: str, name: str):
    d = driver()
    if not d: return
    with d.session() as s:
        s.run("MERGE (p:Project {id:$id}) SET p.name=$name, p.updated_at=timestamp()", id=project_id, name=name)

def create_artifact(project_id: str, a_type: str):
    d = driver()
    if not d: return
    with d.session() as s:
        s.run("""
            MERGE (p:Project {id:$pid})
            CREATE (a:Artifact {id: randomUUID(), type:$t, created_at:timestamp()})
            MERGE (p)-[:PRODUCES]->(a)
        """, pid=project_id, t=a_type)
