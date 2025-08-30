from typing import Dict, Any
from ..crews.adapters import ValidatorAdapter, AdvisoryAdapter
from ..crews.validator_crew import ValidatorCrew
from ..crews.advisory_board_crew import AdvisoryBoardCrew

class AgentRegistry:
    """Registry that returns adapter-wrapped crews."""
    
    def __init__(self):
        self._registry = {}
        self._initialize_registry()
    
    def _initialize_registry(self):
        """Initialize the registry with adapter-wrapped crews."""
        # Create base crews
        validator_crew = ValidatorCrew()
        advisory_crew = AdvisoryBoardCrew()
        
        # Wrap with adapters
        self._registry["validator"] = ValidatorAdapter(validator_crew)
        self._registry["advisory"] = AdvisoryAdapter(advisory_crew)
    
    def get(self, agent_name: str):
        """Get an agent by name."""
        return self._registry.get(agent_name)
    
    def list_agents(self) -> list:
        """List all available agents."""
        return list(self._registry.keys())
    
    def register(self, name: str, agent):
        """Register a new agent."""
        self._registry[name] = agent
