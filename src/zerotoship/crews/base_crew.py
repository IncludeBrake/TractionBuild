"""
Base Crew class for ZeroToShip.
Provides a standardized interface for all crews to ensure consistent method signatures
and proper data flow between the WorkflowEngine and crew implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from crewai import Crew, Agent, Task
import logging
from datetime import datetime
import asyncio

# Retry logic imports
try:
    from tenacity import retry, stop_after_attempt, wait_exponential, RetryError
    TENACITY_AVAILABLE = True
except ImportError:
    TENACITY_AVAILABLE = False
    # Mock retry decorator
    def retry(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    RetryError = Exception

# Import the output serializer
from ..core.output_serializer import output_serializer
from ..models.crew_output import CrewOutputValidator

logger = logging.getLogger(__name__)


class BaseCrew(ABC):
    """
    An abstract base class for all crews in ZeroToShip.
    It standardizes the run_async method signature and ensures that
    crews are instantiated with the necessary project context.
    """
    
    def __init__(self, project_data: Dict[str, Any]):
        """
        Initializes the crew with the current project data.
        
        Args:
            project_data: The full, current state of the project.
        """
        self.project_data = project_data
        self.crew = self._create_crew()  # Subclasses will implement this
        logger.info(f"Initialized {self.__class__.__name__} with project data")

    @abstractmethod
    def _create_crew(self) -> Crew:
        """
        Subclasses must implement this method to define their agents and tasks
        and return an instantiated CrewAI Crew object.
        
        Returns:
            An instantiated CrewAI Crew object
        """
        raise NotImplementedError("Subclasses must implement the _create_crew method.")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry_error_callback=lambda retry_state: logger.warning(f"Crew execution retry {retry_state.attempt_number}")
    ) if TENACITY_AVAILABLE else lambda f: f
    async def run_async(self) -> Dict[str, Any]:
        """
        The standardized entry point for running a crew's tasks.
        It kicks off the CrewAI process with retry logic, sustainability tracking, and proper output serialization.
        
        Returns:
            A dictionary containing the crew's results, properly serialized and enhanced with metadata.
        """
        # Initialize carbon tracking if enabled
        tracker = None
        try:
            from codecarbon import EmissionsTracker
            import os
            
            if os.getenv('CODECARBON_ENABLED', 'false').lower() == 'true':
                project_name = os.getenv('CODECARBON_PROJECT_NAME', f'ZeroToShip_{self.__class__.__name__}')
                tracker = EmissionsTracker(
                    project_name=project_name,
                    measure_power_secs=15,
                    save_to_file=False,
                    logging_logger=logger
                )
                tracker.start()
                logger.info(f"Carbon tracking started for {self.__class__.__name__}")
        except ImportError:
            logger.debug("CodeCarbon not available - sustainability tracking disabled")
        except Exception as e:
            logger.warning(f"Failed to initialize carbon tracking: {e}")
        
        execution_start = datetime.utcnow()
        project_id = self.project_data.get('id', 'unknown')
        
        try:
            logger.info(f"Starting {self.__class__.__name__} execution (attempt with retry logic)")
            
            # Execute the crew with proper input handling
            crew_inputs = self._prepare_crew_inputs()
            result = await self.crew.kickoff_async(inputs=crew_inputs)
            
            # Stop carbon tracking and get emissions
            emissions = 0.0
            energy_consumed = 0.0
            if tracker:
                try:
                    emissions = tracker.stop()
                    energy_consumed = getattr(tracker, 'energy_consumed', 0.0)
                    logger.info(f"{self.__class__.__name__} carbon footprint: {emissions:.6f} kg CO2e")
                except Exception as e:
                    logger.warning(f"Failed to stop carbon tracking: {e}")
            
            # Serialize the crew output properly
            serialized_result = output_serializer.serialize_crew_output(result, project_id)
            
            # Validate serialization
            if not output_serializer.validate_serialization(result, serialized_result):
                logger.warning(f"Serialization validation failed for {self.__class__.__name__}")
            
            # Extract the primary content from serialized result
            content = serialized_result.get('content', {})
            primary_content = content.get('primary_content', content.get('raw', str(result)))
            
            # Best practice: Return the result nested under a key
            # that corresponds to the crew's function.
            output_key = self._get_output_key()
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - execution_start).total_seconds()
            
            # Enhanced result with all metadata
            enhanced_result = {
                output_key: primary_content,
                'serialized_output': serialized_result,
                'execution_metadata': {
                    'crew_name': self.__class__.__name__,
                    'execution_timestamp': execution_start.isoformat(),
                    'execution_duration_seconds': execution_time,
                    'project_id': project_id,
                    'retry_attempt': getattr(self, '_retry_attempt', 1),
                    'serialization_validated': True
                },
                'sustainability': {
                    'co2_emissions_kg': float(emissions) if emissions else 0.0,
                    'energy_consumed_kwh': float(energy_consumed) if energy_consumed else 0.0,
                    'carbon_efficiency_rating': self._calculate_carbon_efficiency(emissions)
                },
                'state_transition': {
                    'next_state': self._determine_next_state(),
                    'conditions_met': True,
                    'transition_timestamp': datetime.utcnow().isoformat()
                }
            }
            
            # Validate and ensure state field is present
            validated_result = CrewOutputValidator.validate_and_enrich(
                enhanced_result, 
                self.__class__.__name__, 
                project_id
            )
            
            logger.info(f"{self.__class__.__name__} completed successfully in {execution_time:.2f}s")
            return validated_result
            
        except (RetryError, Exception) as e:
            # Stop tracker in case of error
            emissions = 0.0
            if tracker:
                try:
                    emissions = tracker.stop()
                except:
                    pass
            
            execution_time = (datetime.utcnow() - execution_start).total_seconds()
            
            # Determine if this is a retry error or direct error
            if isinstance(e, RetryError):
                logger.error(f"{self.__class__.__name__} failed after all retries: {e.last_attempt.exception()}")
                error_msg = f"Failed after retries: {e.last_attempt.exception()}"
                retry_count = e.last_attempt.attempt_number
            else:
                logger.error(f"Error in {self.__class__.__name__}: {e}")
                error_msg = str(e)
                retry_count = 1
            
            # Return structured error response
            error_result = {
                self._get_output_key(): {
                    "error": error_msg,
                    "error_type": type(e).__name__,
                    "status": "failed",
                    "retry_count": retry_count
                },
                'execution_metadata': {
                    'crew_name': self.__class__.__name__,
                    'execution_timestamp': execution_start.isoformat(),
                    'execution_duration_seconds': execution_time,
                    'project_id': project_id,
                    'status': 'error'
                },
                'sustainability': {
                    "co2_emissions_kg": float(emissions) if emissions else 0.0,
                    "energy_consumed_kwh": 0.0,
                    "carbon_efficiency_rating": "error"
                },
                'state_transition': {
                    'next_state': 'ERROR',
                    'conditions_met': False,
                    'error_recovery': True,
                    'transition_timestamp': datetime.utcnow().isoformat()
                }
            }
            
            # Validate error result to ensure state field is present
            validated_error_result = CrewOutputValidator.validate_and_enrich(
                error_result,
                self.__class__.__name__,
                project_id
            )
            
            return validated_error_result

    def _get_output_key(self) -> str:
        """
        Get the output key for this crew's results.
        Defaults to the crew class name in lowercase, with 'crew' removed.
        
        Returns:
            The key under which this crew's results should be stored
        """
        class_name = self.__class__.__name__
        # Convert ValidatorCrew -> validator, MarketingCrew -> marketing, etc.
        return class_name.lower().replace("crew", "")

    def get_project_context(self) -> Dict[str, Any]:
        """
        Get the current project context for use in crew tasks.
        
        Returns:
            A dictionary containing relevant project context
        """
        return {
            "idea": self.project_data.get("idea", ""),
            "project_id": self.project_data.get("id", ""),
            "current_state": self.project_data.get("state", ""),
            "workflow": self.project_data.get("workflow", ""),
            "user_id": self.project_data.get("user_id", ""),
            "created_at": self.project_data.get("created_at", ""),
            "validation": self.project_data.get("validation", {}),
            "marketing": self.project_data.get("marketing", {}),
            "launch": self.project_data.get("launch", {}),
            "build": self.project_data.get("build", {}),
            "feedback": self.project_data.get("feedback", {})
        }

    def update_project_data(self, updates: Dict[str, Any]) -> None:
        """
        Update the project data with new information.
        This is useful for crews that need to modify project state.
        
        Args:
            updates: Dictionary of updates to apply to project_data
        """
        self.project_data.update(updates)
        logger.debug(f"Updated project data with: {updates}")

    def get_crew_info(self) -> Dict[str, Any]:
        """
        Get information about this crew for debugging and monitoring.
        
        Returns:
            Dictionary containing crew information
        """
        return {
            "crew_type": self.__class__.__name__,
            "project_id": self.project_data.get("id", ""),
            "current_state": self.project_data.get("state", ""),
            "output_key": self._get_output_key(),
            "agents_count": len(self.crew.agents) if hasattr(self.crew, 'agents') else 0,
            "tasks_count": len(self.crew.tasks) if hasattr(self.crew, 'tasks') else 0
        }
    
    def _prepare_crew_inputs(self) -> Dict[str, Any]:
        """
        Prepare inputs for crew execution, ensuring all data is serializable.
        
        Returns:
            Serialized project data safe for crew input
        """
        try:
            # Create a clean copy of project data with only serializable values
            clean_inputs = {}
            for key, value in self.project_data.items():
                if isinstance(value, (str, int, float, bool, list, dict, type(None))):
                    clean_inputs[key] = value
                else:
                    # Convert non-serializable objects to strings
                    clean_inputs[key] = str(value)
                    logger.debug(f"Converted {key} to string for crew input")
            
            return clean_inputs
            
        except Exception as e:
            logger.error(f"Failed to prepare crew inputs: {e}")
            # Return minimal safe inputs
            return {
                'idea': self.project_data.get('idea', ''),
                'project_id': self.project_data.get('id', ''),
                'state': self.project_data.get('state', '')
            }
    
    def _determine_next_state(self) -> str:
        """
        Determine the next state based on current crew and project state.
        
        Returns:
            Next workflow state
        """
        current_state = self.project_data.get('state', '')
        crew_name = self.__class__.__name__
        
        # Default state transitions based on crew type
        state_map = {
            'ValidatorCrew': 'FEEDBACK_COLLECTION',
            'FeedbackCrew': 'COMPLETED',
            'MarketingCrew': 'LAUNCH_PREPARATION',
            'LaunchCrew': 'COMPLETED',
            'BuilderCrew': 'TESTING',
            'ExecutionCrew': 'COMPLETED'
        }
        
        return state_map.get(crew_name, 'COMPLETED')
    
    def _calculate_carbon_efficiency(self, emissions: float) -> str:
        """
        Calculate carbon efficiency rating based on emissions.
        
        Args:
            emissions: CO2 emissions in kg
            
        Returns:
            Carbon efficiency rating string
        """
        if emissions < 0.001:
            return 'EXCELLENT'
        elif emissions < 0.005:
            return 'GOOD'
        elif emissions < 0.01:
            return 'FAIR'
        else:
            return 'NEEDS_IMPROVEMENT' 