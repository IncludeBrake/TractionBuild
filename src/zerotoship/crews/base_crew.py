import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any
import os
import copy

from crewai import Crew

# Gracefully import tenacity for retry logic
try:
    from tenacity import retry, stop_after_attempt, wait_exponential, RetryError
    TENACITY_AVAILABLE = True
except ImportError:
    TENACITY_AVAILABLE = False
    def retry(*args, **kwargs):
        def decorator(func): return func
        return decorator
    RetryError = Exception

# Gracefully import codecarbon for sustainability tracking
try:
    from codecarbon import EmissionsTracker
    CODECARBON_AVAILABLE = True
except ImportError:
    CODECARBON_AVAILABLE = False

logger = logging.getLogger(__name__)

class BaseCrew(ABC):
    """
    The abstract base class for all crews in ZeroToShip. It standardizes
    execution by providing built-in retry logic, sustainability tracking,
    structured output, and consistent error handling.
    """
    
    def __init__(self, project_data: Dict[str, Any]):
        """Initializes the crew with the current project context."""
        self.project_data = project_data
        self.crew = self._create_crew() # Implemented by subclasses
        logger.info(f"Initialized {self.__class__.__name__}")

    @abstractmethod
    def _create_crew(self) -> Crew:
        """Subclasses must implement this to define their agents, tasks, and CrewAI crew object."""
        raise NotImplementedError("Subclasses must implement the _create_crew method.")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry_error_callback=lambda retry_state: logger.warning(
            f"Retrying {retry_state.fn.__self__.__class__.__name__} "
            f"(attempt {retry_state.attempt_number})... Reason: {retry_state.outcome.exception()}"
        )
    ) if TENACITY_AVAILABLE else lambda f: f
    async def run_async(self) -> Dict[str, Any]:
        """
        The standardized entry point for running a crew. It handles execution,
        retries, carbon tracking, and returns a structured data delta.
        """
        tracker = None
        if CODECARBON_AVAILABLE and os.getenv('CODECARBON_ENABLED', 'true').lower() == 'true':
            try:
                tracker = EmissionsTracker(project_name=self.__class__.__name__, save_to_file=False, logging_logger=logger)
                tracker.start()
            except Exception as e:
                logger.warning(f"Failed to initialize CodeCarbon tracker: {e}")

        execution_start_time = datetime.utcnow()
        try:
            # Prepare a safe, deep copy of project data for the crew
            crew_inputs = copy.deepcopy(self.project_data)
            
            # The core execution of the CrewAI crew
            raw_result = await self.crew.kickoff_async(inputs=crew_inputs)
            
            # Process and structure the final output
            return self._format_success_output(raw_result, execution_start_time, tracker)

        except Exception as e:
            # Handle any exception, including RetryError from tenacity
            return self._format_error_output(e, execution_start_time, tracker)

    def _get_output_key(self) -> str:
        """Generates a clean dictionary key from the crew's class name."""
        return self.__class__.__name__.lower().replace("crew", "")

    def _format_success_output(self, raw_result: Any, start_time: datetime, tracker) -> Dict[str, Any]:
        """Structures the output for a successful crew execution."""
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Ensure result is a dictionary
        if isinstance(raw_result, str):
            processed_result = {"output": raw_result}
        elif isinstance(raw_result, dict):
            processed_result = raw_result
        else:
            processed_result = {"output": str(raw_result)}

        # Add execution metadata to the result
        processed_result['execution_metadata'] = {
            'crew_name': self.__class__.__name__,
            'timestamp_utc': start_time.isoformat(),
            'duration_seconds': round(execution_time, 2),
            'status': 'completed'
        }

        # Add sustainability metrics if available
        if tracker:
            try:
                emissions_kg = tracker.stop() or 0.0
                processed_result['sustainability'] = {'co2_emissions_kg': emissions_kg}
            except Exception as e:
                logger.warning(f"Failed to stop CodeCarbon tracker: {e}")

        logger.info(f"{self.__class__.__name__} completed successfully in {execution_time:.2f}s.")
        
        # Return the final data delta, nested under the crew's key
        return {self._get_output_key(): processed_result}

    def _format_error_output(self, error: Exception, start_time: datetime, tracker) -> Dict[str, Any]:
        """Structures the output for a failed crew execution."""
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        logger.error(f"{self.__class__.__name__} failed after {execution_time:.2f}s: {error}", exc_info=True)
        
        if tracker:
            try: tracker.stop()
            except: pass

        error_msg = str(error.last_attempt.exception()) if isinstance(error, RetryError) else str(error)

        return {
            "error": {
                "message": error_msg,
                "type": type(error).__name__,
                'crew_name': self.__class__.__name__,
                'duration_seconds': round(execution_time, 2),
                'status': 'failed'
            }
        }