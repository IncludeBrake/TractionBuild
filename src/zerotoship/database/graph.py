from neo4j import AsyncGraphDatabase
from typing import Dict, Any

class GraphDAO:
    def __init__(self, driver: AsyncGraphDatabase.driver):
        self.driver = driver
    
    async def create_project_node(self, project_id: str, project_data: Dict[str, Any]):
        """Create a project node in Neo4j."""
        async with self.driver.session() as session:
            await session.run("""
                CREATE (p:Project {id: $project_id, name: $name, description: $description})
            """, project_id=project_id, name=project_data["name"], description=project_data["description"])
    
    async def create_artifact_node(self, project_id: str, artifact_type: str, artifact_data: Dict[str, Any]):
        """Create an artifact node and link it to the project."""
        async with self.driver.session() as session:
            await session.run("""
                MATCH (p:Project {id: $project_id})
                CREATE (a:Artifact {type: $artifact_type, data: $artifact_data})
                CREATE (p)-[:PRODUCES]->(a)
            """, project_id=project_id, artifact_type=artifact_type, artifact_data=artifact_data)
    
    async def get_project_artifacts(self, project_id: str):
        """Get all artifacts for a project."""
        async with self.driver.session() as session:
            result = await session.run("""
                MATCH (p:Project {id: $project_id})-[:PRODUCES]->(a:Artifact)
                RETURN a.type as type, a.data as data
                ORDER BY a.type
            """, project_id=project_id)
            
            return [{"type": record["type"], "data": record["data"]} async for record in result]
