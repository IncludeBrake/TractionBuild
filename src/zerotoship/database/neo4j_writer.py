import os
import logging
from neo4j import GraphDatabase
from typing import Dict

logger = logging.getLogger(__name__)

class Neo4jWriter:
    """A dedicated writer class for ingesting ZeroToShip events into Neo4j."""
    def __init__(self):
        uri = os.getenv("NEO4J_URI", "neo4j://neo4j:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD")
        if not all([uri, user, password]):
            self._driver = None
            logger.warning("Neo4j credentials not fully configured. Writer will be inactive.")
        else:
            self._driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        if self._driver:
            self._driver.close()

    def write_step_artifact(self, project: Dict, agent_key: str, artifact: Dict):
        """Writes a new artifact produced by an agent for a project."""
        if not self._driver: return

        with self._driver.session() as session:
            session.execute_write(
                self._tx_write_step, project, agent_key, artifact
            )
        logger.info(f"Wrote artifact of kind '{artifact.get('kind')}' from agent '{agent_key}' to graph.")

    @staticmethod
    def _tx_write_step(tx, project: Dict, agent_key: str, artifact: Dict):
        # Ensure project and agent nodes exist
        tx.run("""
            MERGE (p:Project {id: $proj_id})
              ON CREATE SET p.name = $proj_name, p.created_at = timestamp()
            MERGE (g:Agent {name: $agent_name})
            """, proj_id=project["id"], proj_name=project.get("idea", "Untitled"), agent_name=agent_key)
        
        # Create the artifact and link it to the project and agent
        tx.run("""
            MATCH (p:Project {id: $proj_id})
            MATCH (g:Agent {name: $agent_name})
            MERGE (a:Artifact {id: $art_id})
              ON CREATE SET a.kind = $art_kind, a.created_at = timestamp()
            // Set all other properties from the artifact dictionary
            SET a += $art_props
            MERGE (p)-[:PRODUCES]->(a)
            MERGE (g)-[:PRODUCED]->(a)
            """, 
            proj_id=project["id"], 
            agent_name=agent_key,
            art_id=artifact.get("id", f"{project['id']}:{agent_key}:{artifact.get('kind','generic')}"),
            art_kind=artifact.get("kind", "generic"),
            art_props={k: v for k, v in artifact.items() if k not in ["id", "kind"]}
        )

# Create a singleton instance for easy import
neo4j_writer = Neo4jWriter()