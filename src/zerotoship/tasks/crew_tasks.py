"""
Celery tasks for executing tractionbuild crews in a distributed environment.
"""

import asyncio
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime
from celery import current_task
from codecarbon import EmissionsTracker

from .celery_app import app
from ..crews import CREW_REGISTRY
from ..core.project_meta_memory import ProjectMetaMemoryManager
from ..utils.logging import setup_logging

logger = logging.getLogger(__name__)

@app.task(name="execute_crew_task", bind=True)
def execute_crew_task(self, crew_name: str, project_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a specific crew task in a distributed Celery worker.
    
    Args:
        crew_name: Name of the crew to execute
        project_data: Current project state data
        
    Returns:
        Result delta from crew execution with sustainability metrics
    """
    task_id = self.request.id
    start_time = datetime.utcnow()
    
    logger.info(f"Starting crew task {crew_name} with task ID: {task_id}")
    
    # Initialize emissions tracking
    tracker = EmissionsTracker(
        project_name=f"tractionbuild_{crew_name}",
        measure_power_secs=15,  # Measure every 15 seconds
        save_to_file=False,
        logging_logger=logger
    )
    
    try:
        # Update task progress
        self.update_state(
            state='PROGRESS',
            meta={'status': 'Initializing crew', 'progress': 10}
        )
        
        # Get crew class from registry
        crew_class = CREW_REGISTRY.get(crew_name)
        if not crew_class:
            raise ValueError(f"Crew '{crew_name}' not found in registry. Available crews: {list(CREW_REGISTRY.keys())}")
        
        # Start emissions tracking
        tracker.start()
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'status': 'Executing crew tasks', 'progress': 30}
        )
        
        # Instantiate and run crew
        crew_instance = crew_class(project_data)
        
        # Run the async crew execution in the sync Celery task
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result_delta = loop.run_until_complete(crew_instance.run_async())
        finally:
            loop.close()
        
        # Stop emissions tracking
        emissions = tracker.stop()
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'status': 'Processing results', 'progress': 90}
        )
        
        # Add execution metadata
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Enhance result with sustainability and execution metrics
        if isinstance(result_delta, dict):
            result_delta.update({
                'execution_metadata': {
                    'task_id': task_id,
                    'crew_name': crew_name,
                    'execution_time_seconds': execution_time,
                    'worker_id': self.request.hostname,
                    'timestamp': datetime.utcnow().isoformat()
                },
                'sustainability': {
                    'co2_emissions_kg': float(emissions) if emissions else 0.0,
                    'energy_consumed_kwh': getattr(tracker, 'energy_consumed', 0.0),
                    'carbon_intensity': getattr(tracker, 'carbon_intensity', 0.0)
                }
            })
        
        logger.info(f"Crew {crew_name} completed successfully in {execution_time:.2f}s with {emissions:.6f} kg CO2e")
        
        return result_delta
        
    except Exception as e:
        # Stop tracker in case of error
        try:
            emissions = tracker.stop()
        except:
            emissions = 0.0
            
        error_result = {
            'error': str(e),
            'error_type': type(e).__name__,
            'crew_name': crew_name,
            'task_id': task_id,
            'execution_metadata': {
                'task_id': task_id,
                'crew_name': crew_name,
                'execution_time_seconds': (datetime.utcnow() - start_time).total_seconds(),
                'worker_id': self.request.hostname,
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'failed'
            },
            'sustainability': {
                'co2_emissions_kg': float(emissions) if emissions else 0.0
            }
        }
        
        logger.error(f"Crew {crew_name} failed: {e}")
        raise self.retry(countdown=60, max_retries=3, exc=e)


@app.task(name="validate_project_data", bind=True)
def validate_project_data(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate project data structure and requirements.
    
    Args:
        project_data: Project data to validate
        
    Returns:
        Validation results
    """
    try:
        from ..core.schema_validator import is_valid_project_data
        
        validation_result = is_valid_project_data(project_data)
        
        return {
            'valid': validation_result,
            'project_id': project_data.get('id', 'unknown'),
            'timestamp': datetime.utcnow().isoformat(),
            'validator_task_id': self.request.id
        }
        
    except Exception as e:
        logger.error(f"Project data validation failed: {e}")
        return {
            'valid': False,
            'error': str(e),
            'project_id': project_data.get('id', 'unknown'),
            'timestamp': datetime.utcnow().isoformat()
        }


@app.task(name="generate_sustainability_report", bind=True)
def generate_sustainability_report(self, project_id: str, execution_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a comprehensive sustainability report for a project execution.
    
    Args:
        project_id: Project identifier
        execution_data: Execution metadata and sustainability metrics
        
    Returns:
        Sustainability report
    """
    try:
        total_emissions = sum(
            step.get('sustainability', {}).get('co2_emissions_kg', 0.0)
            for step in execution_data.get('execution_history', [])
        )
        
        total_energy = sum(
            step.get('sustainability', {}).get('energy_consumed_kwh', 0.0)
            for step in execution_data.get('execution_history', [])
        )
        
        report = {
            'project_id': project_id,
            'report_generated_at': datetime.utcnow().isoformat(),
            'total_co2_emissions_kg': total_emissions,
            'total_energy_consumed_kwh': total_energy,
            'carbon_efficiency_rating': _calculate_carbon_efficiency(total_emissions, execution_data),
            'sustainability_recommendations': _generate_sustainability_recommendations(total_emissions),
            'compliance_status': 'COMPLIANT' if total_emissions < 0.1 else 'REVIEW_REQUIRED'
        }
        
        logger.info(f"Generated sustainability report for project {project_id}: {total_emissions:.6f} kg CO2e")
        
        return report
        
    except Exception as e:
        logger.error(f"Failed to generate sustainability report: {e}")
        return {
            'project_id': project_id,
            'error': str(e),
            'report_generated_at': datetime.utcnow().isoformat()
        }


def _calculate_carbon_efficiency(emissions: float, execution_data: Dict[str, Any]) -> str:
    """Calculate carbon efficiency rating."""
    if emissions < 0.01:
        return 'EXCELLENT'
    elif emissions < 0.05:
        return 'GOOD'
    elif emissions < 0.1:
        return 'FAIR'
    else:
        return 'NEEDS_IMPROVEMENT'


def _generate_sustainability_recommendations(emissions: float) -> list:
    """Generate sustainability improvement recommendations."""
    recommendations = []
    
    if emissions > 0.1:
        recommendations.append("Consider using more efficient AI models or reducing model complexity")
        recommendations.append("Implement model caching to reduce redundant computations")
    
    if emissions > 0.05:
        recommendations.append("Optimize crew task parallelization to reduce total execution time")
        recommendations.append("Consider using renewable energy sources for compute infrastructure")
    
    recommendations.append("Monitor and track carbon emissions for continuous improvement")
    
    return recommendations