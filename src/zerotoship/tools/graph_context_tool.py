from typing import Dict, Any

class BaseTool:
    """Base tool class for ZeroToShip tools."""
    name: str = "Base Tool"
    description: str = "Base tool description"
    
    def _run(self, *args, **kwargs) -> str:
        raise NotImplementedError("Subclasses must implement _run method")
from ..database.neo4j_writer import neo4j_writer # Reuse the writer's driver for reads

class GraphContextTool(BaseTool):
    name: str = "Project Context Retrieval Tool"
    description: str = "Retrieves relevant artifacts, tasks, and decisions for a given project from the Neo4j graph to provide context for new prompts."

    def _run(self, project_id: str) -> str:
        if not neo4j_writer._driver:
            return "Graph database not connected."
        
        query = """
            MATCH (p:Project {id: $pid})-[:PRODUCES]->(a:Artifact)
            OPTIONAL MATCH (p)-[:HAS_TASK]->(t:Task)
            RETURN 
                a.kind as artifact_kind, a.output as artifact_output, 
                t.title as task_title, t.status as task_status
            ORDER BY a.created_at DESC
            LIMIT 10
        """
        with neo4j_writer._driver.session() as session:
            result = session.run(query, pid=project_id)
            context_str = "Recent Project Context:\n"
            for record in result:
                context_str += f"- Artifact ({record['artifact_kind']}): {str(record['artifact_output'])[:100]}...\n"
                if record['task_title']:
                    context_str += f"  - Related Task: {record['task_title']} ({record['task_status']})\n"
            return context_str