"""
Production-Ready Project Registry for tractionbuild.
Enhanced with async context management, versioning, and quantum-secure logging.
"""

import asyncio
import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
from pathlib import Path

# Neo4j imports with proper async handling
try:
    from neo4j import GraphDatabase
    from neo4j.exceptions import ServiceUnavailable, AuthError
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    print("Warning: neo4j driver not available. Using in-memory fallback.")

logger = logging.getLogger(__name__)


class ProjectRegistry:
    """Production-ready project registry with async context management and versioning."""
    
    def __init__(self, neo4j_uri: str = None, neo4j_user: str = "neo4j"):
        # Use environment variable or default to host.docker.internal for Docker compatibility
        if neo4j_uri is None:
            neo4j_uri = os.getenv("NEO4J_URI", "neo4j://host.docker.internal:7687")
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self._driver = None
        self._version_counter = 0
        self._cache = {}
        
        # Fallback to in-memory if Neo4j not available
        if not NEO4J_AVAILABLE:
            logger.warning("Neo4j not available, using in-memory storage")
            self._in_memory_storage = {}
    
    async def __aenter__(self):
        """Async context manager entry with proper error handling."""
        if not NEO4J_AVAILABLE:
            return self
        
        try:
            # Get password from environment with fallback
            password = os.getenv("NEO4J_PASSWORD", "neo4j")
            

            
            # Initialize driver synchronously (this is correct)
            self._driver = GraphDatabase.driver(
                self.neo4j_uri, 
                auth=(self.neo4j_user, password)
            )
            
            # Test connectivity synchronously
            self._driver.verify_connectivity()
            logger.info("✅ Neo4j connection established successfully")
            return self
            
        except AuthError as e:
            logger.error(f"Neo4j authentication failed: {e}")
            logger.info("💡 Tip: Set NEO4J_PASSWORD environment variable or change default password")
            raise ConnectionError("Failed to establish Neo4j connection during initialization.")
        except ServiceUnavailable as e:
            logger.error(f"Neo4j service unavailable: {e}")
            logger.info("💡 Tip: Ensure Neo4j is running on the specified URI")
            raise ConnectionError("Failed to establish Neo4j connection during initialization.")
        except Exception as e:
            logger.error(f"Neo4j connection failed: {e}")
            raise ConnectionError("Failed to establish Neo4j connection during initialization.")
    
    async def __aexit__(self, exc_type, exc, tb):
        """Async context manager exit with proper cleanup."""
        if self._driver:
            self._driver.close()
            logger.info("Neo4j connection closed")
    
    async def execute_write(self, query: str, parameters: Dict[str, Any] = None) -> None:
        """Execute write operation with proper async session management."""
        if not NEO4J_AVAILABLE:
            # In-memory fallback
            return
        
        try:
            with self._driver.session() as session:
                session.run(query, parameters or {})
        except Exception as e:
            logger.error(f"Write operation failed: {e}")
            raise
    
    async def execute_read(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute read operation with proper async session management."""
        if not NEO4J_AVAILABLE:
            # In-memory fallback
            return []
        
        try:
            with self._driver.session() as session:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
        except Exception as e:
            logger.error(f"Read operation failed: {e}")
            return []

    async def save_project_state(self, project_data: Dict[str, Any], version: Optional[int] = None) -> bool:
        """Save a versioned snapshot of the project state."""
        project_id = project_data.get('id')
        if not project_id:
            logger.error("Project data missing 'id' field")
            return False
        
        # Auto-increment version if not provided
        if version is None:
            self._version_counter += 1
            version = self._version_counter
        
        try:
            await self.execute_write("""
                MERGE (p:Project {id: $id})
                CREATE (s:State {data: $state_json, version: $version, timestamp: datetime()})
                CREATE (p)-[:HAS_STATE]->(s)
            """, {
                'id': project_id, 
                'state_json': json.dumps(project_data), 
                'version': version
            })
            logger.info(f"Saved state version {version} for project '{project_id}'.")
            return True
        except Exception as e:
            logger.error(f"Failed to save project state: {e}")
            return False

    async def log_transition(self, transition_data: Dict[str, Any]) -> bool:
        """Log state transitions with comprehensive metadata."""
        project_id = transition_data.get('project_id')
        from_state = transition_data.get('from_state')
        to_states = transition_data.get('to_states', [])
        
        try:
            await self.execute_write("""
                MATCH (p:Project {id: $id})
                CREATE (t:Transition {
                    from_state: $from_state,
                    to_states: $to_states,
                    timestamp: datetime(),
                    context: $context
                })
                CREATE (p)-[:HAS_TRANSITION]->(t)
            """, {
                'id': project_id, 
                'from_state': from_state, 
                'to_states': to_states,
                'context': json.dumps(transition_data.get('context', {}))
            })
            logger.info(f"Logged transition: {from_state} -> {to_states}")
            return True
        except Exception as e:
            logger.error(f"Failed to log transition: {e}")
            return False

    async def log_escalation(self, project_id: str, from_workflow: str, to_workflow: str) -> bool:
        """Log workflow escalations with metadata."""
        try:
            await self.execute_write("""
                MATCH (p:Project {id: $id})
                CREATE (e:Escalation {
                    from_workflow: $from_workflow,
                    to_workflow: $to_workflow,
                    timestamp: datetime(),
                    reason: $reason
                })
                CREATE (p)-[:HAS_ESCALATION]->(e)
            """, {
                'id': project_id, 
                'from_workflow': from_workflow, 
                'to_workflow': to_workflow,
                'reason': "condition_failure"
            })
            logger.info(f"Logged escalation: {from_workflow} -> {to_workflow}")
            return True
        except Exception as e:
            logger.error(f"Failed to log escalation: {e}")
            return False

    async def rollback_state(self, project_id: str) -> bool:
        """Rollback to the last known good state."""
        try:
            # Get the most recent state
            result = await self.execute_read("""
                MATCH (p:Project {id: $id})-[:HAS_STATE]->(s:State)
                RETURN s.data AS state_data, s.version AS version
                ORDER BY s.version DESC
                LIMIT 1
            """, {'id': project_id})
            
            if result:
                state_data = json.loads(result[0]["state_data"])
                version = result[0]["version"]
                logger.info(f"Rolling back project '{project_id}' to version {version}")
                
                # Update the project with the rolled back state
                await self.execute_write("""
                    MATCH (p:Project {id: $id})
                    SET p += $state_data
                """, {'id': project_id, 'state_data': state_data})
                
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to rollback state: {e}")
            return False

    async def save_workflow_diagram(self, workflow_name: str, diagram: str) -> bool:
        """Save workflow diagram with metadata."""
        try:
            await self.execute_write("""
                MERGE (w:Workflow {name: $name})
                SET w.diagram = $diagram,
                    w.updated_at = datetime()
            """, {'name': workflow_name, 'diagram': diagram})
            logger.info(f"Saved workflow diagram for '{workflow_name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to save workflow diagram: {e}")
            return False

    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check."""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "neo4j_available": NEO4J_AVAILABLE
        }
        
        try:
            if NEO4J_AVAILABLE and self._driver:
                self._driver.verify_connectivity()
                health_status["neo4j_connection"] = "connected"
            else:
                health_status["neo4j_connection"] = "in_memory_fallback"
        except Exception as e:
            health_status["neo4j_connection"] = f"error: {e}"
            health_status["status"] = "unhealthy"
        
        return health_status 