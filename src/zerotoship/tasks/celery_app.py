import os
import logging
from celery import Celery
from celery.signals import task_prerun, task_postrun, task_failure
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Correctly use the 'redis' service name for the broker URL inside Docker
REDIS_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")

# The 'include' tells Celery where to find the task definitions
app = Celery(
    'zerotoship_tasks',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['src.zerotoship.tasks.crew_tasks']
)

# Your production-ready configuration remains the same
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    worker_prefetch_multiplier=1,
    task_acks_late=True
)

# Your excellent monitoring signals remain the same
@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, **kwargs):
    logger.info(f"Task {task.name}[{task_id}] starting.")

@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, state=None, **kwargs):
    logger.info(f"Task {task.name}[{task_id}] finished with state: {state}")

@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, **kwargs):
    logger.error(f"Task {sender.name}[{task_id}] failed: {exception}")

if __name__ == '__main__':
    app.start()