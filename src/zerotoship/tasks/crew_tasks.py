import asyncio
import logging
from typing import Dict, Any
from datetime import datetime

# Gracefully import CodeCarbon
try:
    from codecarbon import EmissionsTracker
    CODECARBON_AVAILABLE = True
except ImportError:
    CODECARBON_AVAILABLE = False

from .celery_app import app
from ..crews import CREW_REGISTRY

logger = logging.getLogger(__name__)

# This is now an ASYNC task, which is the modern standard for Celery + asyncio
@app.task(name="execute_crew_task", bind=True)
async def execute_crew_task(self, crew_name: str, project_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes a specific crew asynchronously in a distributed Celery worker.
    """
    task_id = self.request.id
    start_time = datetime.utcnow()
    logger.info(f"Starting crew task '{crew_name}' with task ID: {task_id}")

    # Use CodeCarbon as a context manager for safety
    emissions = 0.0
    tracker = None
    if CODECARBON_AVAILABLE:
        tracker = EmissionsTracker(project_name=f"ZeroToShip_{crew_name}", save_to_file=False, logging_logger=logger)
        tracker.start()

    try:
        self.update_state(state='PROGRESS', meta={'status': 'Initializing crew', 'progress': 10})
        
        crew_class = CREW_REGISTRY.get(crew_name)
        if not crew_class:
            raise ValueError(f"Crew '{crew_name}' not found in registry.")
        
        self.update_state(state='PROGRESS', meta={'status': 'Executing crew tasks', 'progress': 30})

        crew_instance = crew_class(project_data)
        
        # The asyncio integration is now clean and simple
        result_delta = await crew_instance.run_async()
        
        self.update_state(state='PROGRESS', meta={'status': 'Processing results', 'progress': 90})

        # --- Process successful result ---
        if tracker: emissions = tracker.stop() or 0.0
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Add metadata to the result delta
        if isinstance(result_delta, dict):
            result_delta['execution_metadata'] = {
                'task_id': task_id,
                'crew_name': crew_name,
                'execution_time_seconds': round(execution_time, 2),
                'worker_id': self.request.hostname,
                'status': 'completed'
            }
            result_delta['sustainability'] = {'co2_emissions_kg': float(emissions)}
        
        logger.info(f"Crew '{crew_name}' completed in {execution_time:.2f}s with {emissions:.6f} kg CO2e")
        return result_delta

    except Exception as e:
        if tracker: 
            try: tracker.stop()
            except: pass
        logger.error(f"Crew '{crew_name}' [Task ID: {task_id}] failed: {e}", exc_info=True)
        # Celery's retry mechanism is powerful for transient errors.
        # This will automatically retry the task with exponential backoff.
        raise self.retry(exc=e, countdown=60, max_retries=3)

# (The other utility tasks like validate_project_data and generate_sustainability_report are excellent as-is)
# ...