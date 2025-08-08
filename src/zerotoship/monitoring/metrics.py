"""
Prometheus metrics for ZeroToShip monitoring and observability.
Provides comprehensive metrics for workflow execution, crew performance, and system health.
"""

import time
import logging
from typing import Dict, Any, Optional
from functools import wraps
from datetime import datetime

try:
    from prometheus_client import (
        Summary, Counter, Histogram, Gauge, Info,
        start_http_server, CollectorRegistry, REGISTRY
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    print("Warning: prometheus_client not available. Monitoring disabled.")

logger = logging.getLogger(__name__)

class ZeroToShipMetrics:
    """Centralized metrics collection for ZeroToShip."""
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        self.registry = registry or REGISTRY
        self.metrics_enabled = PROMETHEUS_AVAILABLE
        
        if not self.metrics_enabled:
            logger.warning("Prometheus metrics disabled - prometheus_client not available")
            return
        
        # Workflow execution metrics
        self.workflow_duration = Histogram(
            'zerotoship_workflow_duration_seconds',
            'Time spent executing complete workflows',
            ['workflow_name', 'status'],
            registry=self.registry
        )
        
        self.workflow_executions_total = Counter(
            'zerotoship_workflow_executions_total',
            'Total number of workflow executions',
            ['workflow_name', 'status'],
            registry=self.registry
        )
        
        # Crew execution metrics
        self.crew_duration = Histogram(
            'zerotoship_crew_duration_seconds',
            'Time spent executing individual crews',
            ['crew_name', 'status', 'execution_mode'],
            registry=self.registry
        )
        
        self.crew_executions_total = Counter(
            'zerotoship_crew_executions_total',
            'Total number of crew executions',
            ['crew_name', 'status', 'execution_mode'],
            registry=self.registry
        )
        
        # Task queue metrics (Celery)
        self.celery_tasks_total = Counter(
            'zerotoship_celery_tasks_total',
            'Total number of Celery tasks',
            ['task_name', 'status'],
            registry=self.registry
        )
        
        self.celery_task_duration = Histogram(
            'zerotoship_celery_task_duration_seconds',
            'Duration of Celery task execution',
            ['task_name', 'worker_id'],
            registry=self.registry
        )
        
        # System health metrics
        self.active_workflows = Gauge(
            'zerotoship_active_workflows',
            'Number of currently active workflows',
            registry=self.registry
        )
        
        self.active_crew_executions = Gauge(
            'zerotoship_active_crew_executions',
            'Number of currently executing crews',
            registry=self.registry
        )
        
        # Error tracking
        self.errors_total = Counter(
            'zerotoship_errors_total',
            'Total number of errors',
            ['error_type', 'component'],
            registry=self.registry
        )
        
        # Sustainability metrics
        self.carbon_emissions_total = Counter(
            'zerotoship_carbon_emissions_kg_total',
            'Total carbon emissions in kg CO2e',
            ['crew_name', 'project_id'],
            registry=self.registry
        )
        
        self.energy_consumption_total = Counter(
            'zerotoship_energy_consumption_kwh_total',
            'Total energy consumption in kWh',
            ['crew_name', 'project_id'],
            registry=self.registry
        )
        
        # System information
        self.system_info = Info(
            'zerotoship_system_info',
            'System information',
            registry=self.registry
        )
        
        # Set system info
        self.system_info.info({
            'version': '1.0.0',
            'component': 'zerotoship',
            'startup_time': datetime.utcnow().isoformat()
        })
        
        logger.info("ZeroToShip metrics initialized successfully")
    
    def record_workflow_execution(self, workflow_name: str, duration: float, status: str):
        """Record workflow execution metrics."""
        if not self.metrics_enabled:
            return
            
        self.workflow_duration.labels(
            workflow_name=workflow_name,
            status=status
        ).observe(duration)
        
        self.workflow_executions_total.labels(
            workflow_name=workflow_name,
            status=status
        ).inc()
    
    def record_crew_execution(self, crew_name: str, duration: float, status: str, execution_mode: str = 'local'):
        """Record crew execution metrics."""
        if not self.metrics_enabled:
            return
            
        self.crew_duration.labels(
            crew_name=crew_name,
            status=status,
            execution_mode=execution_mode
        ).observe(duration)
        
        self.crew_executions_total.labels(
            crew_name=crew_name,
            status=status,
            execution_mode=execution_mode
        ).inc()
    
    def record_celery_task(self, task_name: str, duration: float, status: str, worker_id: str):
        """Record Celery task metrics."""
        if not self.metrics_enabled:
            return
            
        self.celery_tasks_total.labels(
            task_name=task_name,
            status=status
        ).inc()
        
        self.celery_task_duration.labels(
            task_name=task_name,
            worker_id=worker_id
        ).observe(duration)
    
    def record_error(self, error_type: str, component: str):
        """Record error occurrence."""
        if not self.metrics_enabled:
            return
            
        self.errors_total.labels(
            error_type=error_type,
            component=component
        ).inc()
    
    def record_sustainability_metrics(self, crew_name: str, project_id: str, 
                                    co2_emissions: float, energy_consumption: float):
        """Record sustainability metrics."""
        if not self.metrics_enabled:
            return
            
        self.carbon_emissions_total.labels(
            crew_name=crew_name,
            project_id=project_id
        ).inc(co2_emissions)
        
        self.energy_consumption_total.labels(
            crew_name=crew_name,
            project_id=project_id
        ).inc(energy_consumption)
    
    def set_active_workflows(self, count: int):
        """Set the number of active workflows."""
        if not self.metrics_enabled:
            return
        self.active_workflows.set(count)
    
    def set_active_crew_executions(self, count: int):
        """Set the number of active crew executions."""
        if not self.metrics_enabled:
            return
        self.active_crew_executions.set(count)
    
    def start_metrics_server(self, port: int = 8000):
        """Start Prometheus metrics HTTP server."""
        if not self.metrics_enabled:
            logger.warning("Cannot start metrics server - Prometheus not available")
            return False
            
        try:
            start_http_server(port, registry=self.registry)
            logger.info(f"Prometheus metrics server started on port {port}")
            return True
        except Exception as e:
            logger.error(f"Failed to start metrics server: {e}")
            return False


# Global metrics instance
metrics = ZeroToShipMetrics()


def track_execution_time(metric_name: str, labels: Dict[str, str] = None):
    """Decorator to track execution time of functions."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not metrics.metrics_enabled:
                return await func(*args, **kwargs)
                
            start_time = time.time()
            status = 'success'
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = 'error'
                raise
            finally:
                duration = time.time() - start_time
                if metric_name == 'workflow':
                    workflow_name = labels.get('workflow_name', 'unknown') if labels else 'unknown'
                    metrics.record_workflow_execution(workflow_name, duration, status)
                elif metric_name == 'crew':
                    crew_name = labels.get('crew_name', 'unknown') if labels else 'unknown'
                    execution_mode = labels.get('execution_mode', 'local') if labels else 'local'
                    metrics.record_crew_execution(crew_name, duration, status, execution_mode)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not metrics.metrics_enabled:
                return func(*args, **kwargs)
                
            start_time = time.time()
            status = 'success'
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = 'error'
                raise
            finally:
                duration = time.time() - start_time
                if metric_name == 'celery_task':
                    task_name = labels.get('task_name', 'unknown') if labels else 'unknown'
                    worker_id = labels.get('worker_id', 'unknown') if labels else 'unknown'
                    metrics.record_celery_task(task_name, duration, status, worker_id)
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator