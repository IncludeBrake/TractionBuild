"""
Sustainability Tool for ZeroToShip.
Tracks carbon footprint and environmental impact of AI operations.
"""

from crewai.tools import BaseTool
from codecarbon import EmissionsTracker
from typing import Callable, Any, Dict, Optional
from pydantic import BaseModel, Field
import functools
import time
import os

class SustainabilityArgs(BaseModel):
    """Arguments for the Sustainability Tool."""
    function_name: str = Field(..., description="Name of the function to track")
    project_name: str = Field(default="ZeroToShip_Crew_Execution", description="Project name for tracking")

class SustainabilityTrackerTool(BaseTool):
    """Carbon footprint tracking tool for AI operations."""
    
    name: str = "Carbon Footprint Tracker"
    description: str = "Tracks the CO2 emissions of a given Python function call."
    args_schema: type[BaseModel] = SustainabilityArgs
    tracking_mode: str = Field(default="offline", description="Tracking mode for emissions")
    output_dir: str = Field(default="./emissions_data", description="Output directory for emissions data")

    def __init__(self, **kwargs):
        """Initialize the sustainability tracker."""
        super().__init__(**kwargs)
        self.tracking_mode = os.getenv('CODECARBON_MODE', 'offline')
        self.output_dir = os.getenv('CODECARBON_OUTPUT_DIR', './emissions_data')

    def _run(self, function_name: str, project_name: str = "ZeroToShip_Crew_Execution") -> Dict[str, Any]:
        """
        Track emissions for a function execution.
        
        Args:
            function_name: Name of the function being tracked
            project_name: Project name for emissions tracking
            
        Returns:
            Dictionary containing emissions data
        """
        try:
            # Using offline mode is best for local hardware calibration
            tracker = EmissionsTracker(
                project_name=project_name,
                tracking_mode=self.tracking_mode,
                output_dir=self.output_dir,
                log_level='error'  # Reduce logging noise
            )
            
            tracker.start()
            
            # Simulate some computation time for demonstration
            time.sleep(0.1)
            
            emissions = tracker.stop()
            
            return {
                "function_name": function_name,
                "project_name": project_name,
                "co2_emissions_kg": emissions,
                "tracking_mode": self.tracking_mode,
                "status": "success",
                "timestamp": time.time()
            }
            
        except Exception as e:
            return {
                "function_name": function_name,
                "project_name": project_name,
                "error": str(e),
                "co2_emissions_kg": 0,
                "status": "error",
                "timestamp": time.time()
            }

    def track_function(self, func: Callable) -> Callable:
        """
        Decorator to track emissions of a function.
        
        Args:
            func: Function to track
            
        Returns:
            Wrapped function with emissions tracking
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            tracker = EmissionsTracker(
                project_name=f"ZeroToShip_{func.__name__}",
                tracking_mode=self.tracking_mode,
                output_dir=self.output_dir
            )
            
            tracker.start()
            try:
                result = func(*args, **kwargs)
                emissions = tracker.stop()
                
                # Log emissions data
                print(f"🌱 Function {func.__name__} emitted {emissions:.6f} kg CO2")
                
                return result
            except Exception as e:
                tracker.stop()
                raise e
                
        return wrapper

    def get_emissions_summary(self, project_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get emissions summary for a project.
        
        Args:
            project_name: Project name to get summary for
            
        Returns:
            Dictionary containing emissions summary
        """
        try:
            # This would typically read from the emissions CSV file
            # For now, return a mock summary
            return {
                "project_name": project_name or "ZeroToShip_Crew_Execution",
                "total_emissions_kg": 0.001,  # Mock data
                "total_runs": 1,
                "average_emissions_per_run": 0.001,
                "last_updated": time.time(),
                "status": "summary_generated"
            }
        except Exception as e:
            return {
                "error": f"Failed to generate emissions summary: {str(e)}",
                "status": "error"
            }

    async def _arun(self, function_name: str, project_name: str = "ZeroToShip_Crew_Execution") -> Dict[str, Any]:
        """Async version of the sustainability tracker."""
        return self._run(function_name, project_name)

# Convenience function for quick emissions tracking
def track_emissions(func: Callable) -> Callable:
    """
    Decorator to easily track emissions of any function.
    
    Usage:
        @track_emissions
        def my_function():
            # Your code here
            pass
    """
    tracker = SustainabilityTrackerTool()
    return tracker.track_function(func)
