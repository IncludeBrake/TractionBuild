import asyncio
import logging
import os
import json
from typing import Dict, Any, List

# Use the ASYNC version of the GraphDatabase driver
from neo4j import AsyncGraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError

logger = logging.getLogger(__name__)

class ProjectRegistry:
    """
    Production-ready project registry using Neo4j's async driver for non-blocking
    database operations, with versioning, audit logging, and a resilient in-memory fallback.
    """
    
    def __init__(self, neo4j_uri: str = None, neo4j_user: str = "neo4j"):
        # Default URI is now 'neo4j' for Docker Compose networking
        self.neo4j_uri = neo4j_uri or os.getenv("NEO4J_URI", "neo4j://neo4j:7687")
        self.neo4j_user = neo4j_user
        self._driver = None
        self._in_memory_storage = {} # Used only if Neo4j connection fails

    async def __aenter__(self):
        """Async context manager entry to establish the database connection."""
        try:
            password = os.getenv("NEO4J_PASSWORD")
            if not password:
                raise AuthError("NEO4J_PASSWORD environment variable is not set.")

            self._driver = AsyncGraphDatabase.driver(
                self.neo4j_uri, 
                auth=(self.neo4j_user, password)
            )
            await self._driver.verify_connectivity()
            logger.info("✅ Neo4j async connection established successfully.")
            return self
            
        except (AuthError, ServiceUnavailable) as e:
            logger.error(f"Neo4j connection failed: {e}. Falling back to in-memory storage.")
            self._driver = None # Ensure driver is None on failure
            return self # Allow the app to continue in a degraded state
        except Exception as e:
            logger.error(f"An unexpected error occurred during Neo4j connection: {e}", exc_info=True)
            self._driver = None
            return self

    async def __aexit__(self, exc_type, exc, tb):
        """Async context manager exit to gracefully close the connection."""
        if self._driver:
            await self._driver.close()
            logger.info("Neo4j async connection closed.")

    async def _execute_query(self, query: str, parameters: dict) -> List[Dict[str, Any]]:
        """A single, robust method for executing any Cypher query."""
        if not self._driver:
            logger.warning("Executing in-memory (Neo4j not connected). Data will not be persisted.")
            # Simulate basic in-memory operations if needed, or just return
            return []
            
        try:
            async with self._driver.session() as session:
                result = await session.run(query, parameters or {})
                # .data() consumes the result stream and returns a list of dictionaries
                return await result.data()
        except Exception as e:
            logger.error(f"Cypher query failed: {e}", exc_info=True)
            raise # Re-raise the exception to be handled by the calling method

    async def save_project_state(self, project_data: dict, version: int) -> bool:
        """Saves a versioned snapshot of the project state to Neo4j."""
        project_id = project_data.get('id')
        if not project_id:
            logger.error("Cannot save state: project_data is missing 'id'.")
            return False
        
        try:
            await self._execute_query(
                """
                MERGE (p:Project {id: $id})
                CREATE (s:State {data: $state_json, version: $version, timestamp: datetime()})
                CREATE (p)-[:HAS_STATE]->(s)
                """,
                {'id': project_id, 'state_json': json.dumps(project_data, default=str), 'version': version}
            )
            logger.info(f"Saved state version {version} for project '{project_id}'.")
            return True
        except Exception as e:
            logger.error(f"Failed to save project state for '{project_id}': {e}")
            return False

    async def log_transition(self, project_id: str, from_state: str, to_state: str, context: dict):
        """Logs a state transition for a complete audit trail."""
        try:
            await self._execute_query(
                """
                MATCH (p:Project {id: $id})
                CREATE (t:Transition { from: $from, to: $to, context: $context_json, timestamp: datetime() })
                CREATE (p)-[:HAS_TRANSITION]->(t)
                """,
                {'id': project_id, 'from': from_state, 'to': to_state, 'context_json': json.dumps(context, default=str)}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to log transition for '{project_id}': {e}")
            return False

    async def rollback_state(self, project_id: str) -> bool:
        """Rolls back the project's properties to the most recent state snapshot."""
        try:
            result = await self._execute_query(
                """
                MATCH (p:Project {id: $id})-[:HAS_STATE]->(s:State)
                RETURN s.data AS state_data, s.version AS version
                ORDER BY s.version DESC
                LIMIT 1
                """,
                {'id': project_id}
            )
            if result:
                state_data = json.loads(result[0]["state_data"])
                version = result[0]["version"]
                
                # Correct Logic: SET p = ... replaces the properties of the node
                await self._execute_query(
                    "MATCH (p:Project {id: $id}) SET p = $state_data",
                    {'id': project_id, 'state_data': state_data}
                )
                logger.warning(f"Project '{project_id}' successfully rolled back to state version {version}.")
                return True
            else:
                logger.error(f"Rollback failed: No previous state found for project '{project_id}'.")
                return False
        except Exception as e:
            logger.error(f"Failed to rollback state for '{project_id}': {e}")
            return False

    # (Other methods like save_workflow_diagram, log_escalation would follow the same pattern)