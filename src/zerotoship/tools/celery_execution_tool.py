"""
Celery Execution Tool for ZeroToShip.
Provides distributed task execution and monitoring capabilities.
"""

from crewai.tools import BaseTool
from celery import Celery
from typing import Dict, Any, Optional, Callable
from pydantic import BaseModel, Field
import json
import time
import os

class CeleryExecutionArgs(BaseModel):
    """Arguments for the Celery Execution Tool."""
    task_name: str = Field(..., description="Name of the task to execute")
    task_args: list = Field(default=[], description="Arguments for the task")
    task_kwargs: dict = Field(default={}, description="Keyword arguments for the task")
    queue: str = Field(default="default", description="Queue to send the task to")

class CeleryExecutionTool(BaseTool):
    """Distributed task execution tool using Celery."""
    
    name: str = "Celery Task Executor"
    description: str = "Executes tasks asynchronously using Celery for distributed processing."
    args_schema: type[BaseModel] = CeleryExecutionArgs

    def __init__(self):
        """Initialize the Celery client."""
        super().__init__()
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self.celery_app = Celery(
            'zerotoship',
            broker=redis_url,
            backend=redis_url
        )
        
        # Configure Celery
        self.celery_app.conf.update(
            task_serializer='json',
            accept_content=['json'],
            result_serializer='json',
            timezone='UTC',
            enable_utc=True,
            task_track_started=True,
            task_time_limit=30 * 60,  # 30 minutes
            task_soft_time_limit=25 * 60,  # 25 minutes
        )

    def _run(self, task_name: str, task_args: list = None, task_kwargs: dict = None, queue: str = "default") -> Dict[str, Any]:
        """
        Execute a task asynchronously using Celery.
        
        Args:
            task_name: Name of the task to execute
            task_args: Arguments for the task
            task_kwargs: Keyword arguments for the task
            queue: Queue to send the task to
            
        Returns:
            Dictionary containing task information and status
        """
        try:
            task_args = task_args or []
            task_kwargs = task_kwargs or {}
            
            # Send task to Celery
            task = self.celery_app.send_task(
                task_name,
                args=task_args,
                kwargs=task_kwargs,
                queue=queue
            )
            
            return {
                "task_id": task.id,
                "task_name": task_name,
                "status": "PENDING",
                "queue": queue,
                "args": task_args,
                "kwargs": task_kwargs,
                "timestamp": time.time(),
                "message": f"Task {task_name} sent to queue {queue}"
            }
            
        except Exception as e:
            return {
                "error": f"Failed to execute task {task_name}: {str(e)}",
                "task_name": task_name,
                "status": "ERROR",
                "timestamp": time.time()
            }

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get the status of a Celery task.
        
        Args:
            task_id: ID of the task to check
            
        Returns:
            Dictionary containing task status and result
        """
        try:
            task_result = self.celery_app.AsyncResult(task_id)
            
            status_info = {
                "task_id": task_id,
                "status": task_result.status,
                "timestamp": time.time()
            }
            
            if task_result.ready():
                if task_result.successful():
                    status_info["result"] = task_result.result
                    status_info["message"] = "Task completed successfully"
                else:
                    status_info["error"] = str(task_result.info)
                    status_info["message"] = "Task failed"
            else:
                status_info["message"] = f"Task is {task_result.status}"
                
            return status_info
            
        except Exception as e:
            return {
                "error": f"Failed to get task status: {str(e)}",
                "task_id": task_id,
                "status": "ERROR",
                "timestamp": time.time()
            }

    def revoke_task(self, task_id: str, terminate: bool = False) -> Dict[str, Any]:
        """
        Revoke a running Celery task.
        
        Args:
            task_id: ID of the task to revoke
            terminate: Whether to terminate the task immediately
            
        Returns:
            Dictionary containing revocation status
        """
        try:
            self.celery_app.control.revoke(task_id, terminate=terminate)
            
            return {
                "task_id": task_id,
                "action": "revoked",
                "terminate": terminate,
                "message": f"Task {task_id} revoked successfully",
                "timestamp": time.time()
            }
            
        except Exception as e:
            return {
                "error": f"Failed to revoke task {task_id}: {str(e)}",
                "task_id": task_id,
                "action": "revoke_failed",
                "timestamp": time.time()
            }

    def get_queue_stats(self, queue: str = "default") -> Dict[str, Any]:
        """
        Get statistics for a Celery queue.
        
        Args:
            queue: Name of the queue to get stats for
            
        Returns:
            Dictionary containing queue statistics
        """
        try:
            # Get active tasks
            active_tasks = self.celery_app.control.inspect().active()
            
            # Get reserved tasks
            reserved_tasks = self.celery_app.control.inspect().reserved()
            
            # Count tasks in the specified queue
            active_count = 0
            reserved_count = 0
            
            if active_tasks:
                for worker, tasks in active_tasks.items():
                    active_count += len([t for t in tasks if t.get('delivery_info', {}).get('routing_key') == queue])
                    
            if reserved_tasks:
                for worker, tasks in reserved_tasks.items():
                    reserved_count += len([t for t in tasks if t.get('delivery_info', {}).get('routing_key') == queue])
            
            return {
                "queue": queue,
                "active_tasks": active_count,
                "reserved_tasks": reserved_count,
                "total_tasks": active_count + reserved_count,
                "timestamp": time.time()
            }
            
        except Exception as e:
            return {
                "error": f"Failed to get queue stats: {str(e)}",
                "queue": queue,
                "timestamp": time.time()
            }

    async def _arun(self, task_name: str, task_args: list = None, task_kwargs: dict = None, queue: str = "default") -> Dict[str, Any]:
        """Async version of the Celery execution tool."""
        return self._run(task_name, task_args, task_kwargs, queue)
