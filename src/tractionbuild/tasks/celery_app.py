"""
Celery application configuration for tractionbuild.
Enables distributed task execution across multiple workers with Redis as the message broker.
"""

import os
import asyncio
import logging
from typing import Dict, Any, Optional
from celery import Celery
from celery.signals import task_prerun, task_postrun, task_failure
from datetime import datetime
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Configure Celery application
app = Celery(
    'tractionbuild_tasks',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['src.tractionbuild.tasks.crew_tasks']
)

# Celery configuration
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=False,
    task_routes={
        'execute_crew_task': {'queue': 'crew_execution'},
        'validate_project_data': {'queue': 'validation'},
        'generate_report': {'queue': 'reporting'}
    }
)

# Monitoring and metrics
@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds):
    """Log task start for monitoring."""
    logger.info(f"Task {task.name}[{task_id}] started at {datetime.utcnow()}")

@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **kwds):
    """Log task completion for monitoring."""
    logger.info(f"Task {task.name}[{task_id}] completed with state: {state}")

@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, einfo=None, **kwds):
    """Log task failures for monitoring."""
    logger.error(f"Task {sender.name}[{task_id}] failed: {exception}")

if __name__ == '__main__':
    app.start()