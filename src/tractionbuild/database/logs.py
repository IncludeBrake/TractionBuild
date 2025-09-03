import asyncpg
from typing import Dict, Any
from datetime import datetime

class ExecutionLogsDAO:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
    
    async def log_execution(self, project_id: str, agent_name: str, status: str, 
                          duration_ms: int, result: Dict[str, Any] = None, error: str = None):
        """Log an agent execution."""
        now = datetime.utcnow()
        
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO execution_logs (project_id, agent_name, status, duration_ms, result, error, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, project_id, agent_name, status, duration_ms, result, error, now)
    
    async def get_project_logs(self, project_id: str):
        """Get all execution logs for a project."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT agent_name, status, duration_ms, result, error, created_at
                FROM execution_logs 
                WHERE project_id = $1 
                ORDER BY created_at ASC
            """, project_id)
            
            return [dict(row) for row in rows]
