"""
Crew Output Models for ZeroToShip.
Ensures consistent output structure and state management across all crews.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, validator
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ExecutionMetadata(BaseModel):
    """Metadata about crew execution."""
    crew_name: str = Field(..., description="Name of the crew that executed")
    execution_timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    execution_duration_seconds: float = Field(..., description="Execution time in seconds")
    project_id: str = Field(..., description="Project ID")
    retry_attempt: int = Field(default=1, description="Retry attempt number")
    serialization_validated: bool = Field(default=True, description="Whether serialization was validated")
    status: str = Field(default="success", description="Execution status")


class SustainabilityMetrics(BaseModel):
    """Sustainability metrics for crew execution."""
    co2_emissions_kg: float = Field(default=0.0, description="CO2 emissions in kg")
    energy_consumed_kwh: float = Field(default=0.0, description="Energy consumed in kWh")
    carbon_efficiency_rating: str = Field(default="unknown", description="Carbon efficiency rating")


class StateTransition(BaseModel):
    """State transition information."""
    next_state: str = Field(..., description="Next state in the workflow")
    conditions_met: bool = Field(default=True, description="Whether conditions were met")
    transition_timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    error_recovery: bool = Field(default=False, description="Whether this was an error recovery")


class CrewOutput(BaseModel):
    """Standardized crew output with state management."""
    # Primary content from crew execution
    content: Dict[str, Any] = Field(..., description="Primary content from crew execution")
    
    # Metadata
    execution_metadata: ExecutionMetadata = Field(..., description="Execution metadata")
    sustainability: SustainabilityMetrics = Field(..., description="Sustainability metrics")
    state_transition: StateTransition = Field(..., description="State transition information")
    
    # Optional fields
    serialized_output: Optional[Dict[str, Any]] = Field(None, description="Serialized output")
    error: Optional[str] = Field(None, description="Error message if execution failed")
    
    @validator('content', pre=True)
    def ensure_content_dict(cls, v):
        """Ensure content is always a dictionary."""
        if not isinstance(v, dict):
            return {"raw_content": str(v)}
        return v
    
    @validator('state_transition')
    def validate_state_transition(cls, v):
        """Validate state transition."""
        if not v.next_state:
            logger.warning("State transition missing next_state, defaulting to COMPLETED")
            v.next_state = "COMPLETED"
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with state field for workflow engine."""
        result = self.dict()
        
        # Ensure state field is present for workflow engine
        if 'state' not in result:
            result['state'] = self.state_transition.next_state
        
        return result


class CrewOutputValidator:
    """Validator for crew outputs to ensure consistency."""
    
    @staticmethod
    def validate_and_enrich(output: Dict[str, Any], crew_name: str, project_id: str) -> Dict[str, Any]:
        """
        Validate and enrich crew output with required fields.
        
        Args:
            output: Raw crew output
            crew_name: Name of the crew
            project_id: Project ID
            
        Returns:
            Enriched and validated output
        """
        try:
            # If output is already a CrewOutput instance, convert to dict
            if isinstance(output, CrewOutput):
                return output.to_dict()
            
            # Ensure output is a dictionary
            if not isinstance(output, dict):
                output = {"content": {"raw_content": str(output)}}
            
            # Extract execution time if available
            execution_time = output.get('execution_metadata', {}).get('execution_duration_seconds', 0.0)
            
            # Create standardized output
            crew_output = CrewOutput(
                content=output.get('content', output),
                execution_metadata=ExecutionMetadata(
                    crew_name=crew_name,
                    execution_duration_seconds=execution_time,
                    project_id=project_id
                ),
                sustainability=SustainabilityMetrics(),
                state_transition=StateTransition(
                    next_state=output.get('state', 'COMPLETED')
                ),
                serialized_output=output.get('serialized_output'),
                error=output.get('error')
            )
            
            return crew_output.to_dict()
            
        except Exception as e:
            logger.error(f"Error validating crew output: {e}")
            # Return safe fallback
            return {
                "content": {"error": "Output validation failed"},
                "state": "ERROR",
                "execution_metadata": {
                    "crew_name": crew_name,
                    "execution_duration_seconds": 0.0,
                    "project_id": project_id,
                    "status": "error"
                },
                "sustainability": {
                    "co2_emissions_kg": 0.0,
                    "energy_consumed_kwh": 0.0,
                    "carbon_efficiency_rating": "error"
                },
                "state_transition": {
                    "next_state": "ERROR",
                    "conditions_met": False,
                    "error_recovery": True
                }
            }
    
    @staticmethod
    def ensure_state_field(output: Dict[str, Any], current_state: str = "COMPLETED") -> Dict[str, Any]:
        """
        Ensure output has a state field.
        
        Args:
            output: Crew output
            current_state: Current state if not found in output
            
        Returns:
            Output with guaranteed state field
        """
        if not isinstance(output, dict):
            return {"state": current_state, "content": {"raw_content": str(output)}}
        
        if 'state' not in output or not output['state']:
            output['state'] = current_state
        
        return output
