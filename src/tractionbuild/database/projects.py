import asyncpg
from typing import Dict, Any, Optional
from datetime import datetime
import uuid
from ..schemas import Project, ProjectCreate, ProjectStatus

class ProjectsDAO:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
    
    async def create_project(self, project_data: ProjectCreate) -> Project:
        """Create a new project and return the Project object."""
        project_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO projects (id, name, description, state, created_at, updated_at, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, project_id, project_data.name, project_data.description, 
                 ProjectStatus.IDEA_VALIDATION.value, now, now, 
                 {"hypothesis": project_data.hypothesis, "target_avatars": [a.value for a in project_data.target_avatars]})
        
        return Project(
            id=project_id,
            name=project_data.name,
            description=project_data.description,
            state=ProjectStatus.IDEA_VALIDATION,
            created_at=now,
            updated_at=now,
            metadata={"hypothesis": project_data.hypothesis, "target_avatars": [a.value for a in project_data.target_avatars]}
        )
    
    async def get_project(self, project_id: str) -> Optional[Project]:
        """Get a project by ID."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT id, name, description, state, created_at, updated_at, metadata, results
                FROM projects WHERE id = $1
            """, project_id)
            
            if not row:
                return None
            
            return Project(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                state=ProjectStatus(row['state']),
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                metadata=row['metadata'] or {},
                results=row['results'] or {}
            )
    
    async def update_project_state(self, project_id: str, state: ProjectStatus, results: Optional[Dict[str, Any]] = None):
        """Update project state and optionally results."""
        now = datetime.utcnow()
        
        async with self.pool.acquire() as conn:
            if results:
                await conn.execute("""
                    UPDATE projects SET state = $1, updated_at = $2, results = $3
                    WHERE id = $4
                """, state.value, now, results, project_id)
            else:
                await conn.execute("""
                    UPDATE projects SET state = $1, updated_at = $2
                    WHERE id = $4
                """, state.value, now, project_id)
