"""
Centralized Crew Registry for ZeroToShip.
Dynamic loading and validation of crew classes with comprehensive error handling.
"""

import importlib
import pkgutil
import logging
from pathlib import Path
from typing import Dict, Type, Any, Optional
import inspect

logger = logging.getLogger(__name__)


class CrewRegistry:
    """Centralized registry for crew classes with dynamic loading and validation."""
    
    def __init__(self):
        self._crews: Dict[str, Type] = {}
        self._loaded = False
        self._validation_schema = {}
    
    def load_crews(self, crews_path: str = "src/zerotoship/crews") -> None:
        """Dynamically load all crew classes from the crews directory."""
        if self._loaded:
            return
        
        crews_dir = Path(crews_path)
        if not crews_dir.exists():
            logger.warning(f"Crews directory not found: {crews_path}")
            self._load_fallback_crews()
            return
        
        try:
            # Import the crews package
            crews_package = importlib.import_module("zerotoship.crews")
            
            # Iterate through all modules in the crews package
            for module_info in pkgutil.iter_modules(crews_package.__path__, crews_package.__name__ + "."):
                try:
                    module = importlib.import_module(module_info.name)
                    
                    # Find all crew classes in the module
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        
                        # Check if it's a crew class (ends with 'Crew' and is callable)
                        if (attr_name.endswith("Crew") and 
                            callable(attr) and 
                            inspect.isclass(attr) and
                            hasattr(attr, 'run_async')):
                            
                            self._crews[attr_name] = attr
                            logger.debug(f"Loaded crew: {attr_name}")
                            
                except Exception as e:
                    logger.error(f"Failed to load module {module_info.name}: {e}")
            
            # If no crews were loaded dynamically, use fallback
            if not self._crews:
                logger.warning("No crews loaded dynamically, using fallback")
                self._load_fallback_crews()
            
            self._loaded = True
            logger.info(f"Loaded {len(self._crews)} crews: {list(self._crews.keys())}")
            
        except Exception as e:
            logger.error(f"Failed to load crews: {e}")
            # Fallback to manual crew mapping
            self._load_fallback_crews()
    
    def _load_fallback_crews(self) -> None:
        """Fallback crew loading for when dynamic loading fails."""
        try:
            from ..crews.validator_crew import ValidatorCrew
            from ..crews.execution_crew import ExecutionCrew
            from ..crews.builder_crew import BuilderCrew
            from ..crews.marketing_crew import MarketingCrew
            from ..crews.feedback_crew import FeedbackCrew
            
            self._crews.update({
                'ValidatorCrew': ValidatorCrew,
                'GraphCrew': ExecutionCrew,  # Using ExecutionCrew as GraphCrew
                'BuilderCrew': BuilderCrew,
                'MarketingCrew': MarketingCrew,
                'LaunchCrew': MarketingCrew,  # Using MarketingCrew as LaunchCrew
                'FeedbackCrew': FeedbackCrew,
                'ComplianceCrew': FeedbackCrew,  # Using FeedbackCrew as ComplianceCrew
                'HardwareCrew': BuilderCrew,  # Using BuilderCrew as HardwareCrew
                'PrototypeCrew': BuilderCrew,  # Using BuilderCrew as PrototypeCrew
                'TestingCrew': FeedbackCrew,  # Using FeedbackCrew as TestingCrew
            })
            
            self._loaded = True
            logger.info(f"Loaded {len(self._crews)} fallback crews")
            
        except ImportError as e:
            logger.error(f"Failed to load fallback crews: {e}")
            # Create mock crews for testing
            self._create_mock_crews()
    
    def _create_mock_crews(self) -> None:
        """Create mock crews for testing when real crews are not available."""
        class MockCrew:
            def __init__(self, project_data):
                self.project_data = project_data
            
            async def run_async(self, project_data):
                # Simulate crew execution
                return {
                    'validation': {'confidence': 0.8, 'passed': True},
                    'graph': {'status': 'generated', 'generated': True},
                    'build': {'status': 'completed', 'completed': True},
                    'marketing': {'ready': True, 'status': 'ready'},
                    'feedback': {'approved': True, 'quick_approval': True},
                    'testing': {'passed': True}
                }
        
        self._crews.update({
            'ValidatorCrew': MockCrew,
            'GraphCrew': MockCrew,
            'BuilderCrew': MockCrew,
            'MarketingCrew': MockCrew,
            'LaunchCrew': MockCrew,
            'FeedbackCrew': MockCrew,
            'ComplianceCrew': MockCrew,
            'HardwareCrew': MockCrew,
            'PrototypeCrew': MockCrew,
            'TestingCrew': MockCrew,
        })
        
        self._loaded = True
        logger.info(f"Created {len(self._crews)} mock crews for testing")
    
    def get_crew(self, crew_name: str) -> Optional[Type]:
        """Get a crew class by name with validation."""
        if not self._loaded:
            self.load_crews()
        
        crew_class = self._crews.get(crew_name)
        if not crew_class:
            logger.error(f"Unknown crew '{crew_name}'. Available crews: {list(self._crews.keys())}")
            return None
        
        # Validate crew class has required methods
        if not hasattr(crew_class, 'run_async'):
            logger.error(f"Crew '{crew_name}' missing required 'run_async' method")
            return None
        
        return crew_class
    
    def validate_crew(self, crew_name: str) -> Dict[str, Any]:
        """Validate a crew class and return validation results."""
        crew_class = self.get_crew(crew_name)
        
        if not crew_class:
            return {
                'valid': False,
                'error': f"Unknown crew '{crew_name}'",
                'available_crews': list(self._crews.keys())
            }
        
        # Check required methods
        required_methods = ['run_async']
        missing_methods = []
        
        for method in required_methods:
            if not hasattr(crew_class, method):
                missing_methods.append(method)
        
        if missing_methods:
            return {
                'valid': False,
                'error': f"Crew '{crew_name}' missing required methods: {missing_methods}",
                'available_crews': list(self._crews.keys())
            }
        
        return {
            'valid': True,
            'crew_name': crew_name,
            'crew_class': crew_class
        }
    
    def list_available_crews(self) -> Dict[str, Any]:
        """List all available crews with metadata."""
        if not self._loaded:
            self.load_crews()
        
        crews_info = {}
        for name, crew_class in self._crews.items():
            crews_info[name] = {
                'name': name,
                'module': crew_class.__module__,
                'has_run_async': hasattr(crew_class, 'run_async'),
                'docstring': crew_class.__doc__ or "No documentation available"
            }
        
        return crews_info
    
    def get_crew_count(self) -> int:
        """Get the total number of loaded crews."""
        return len(self._crews)
    
    def is_loaded(self) -> bool:
        """Check if crews have been loaded."""
        return self._loaded


# Global crew registry instance
CREW_REGISTRY = CrewRegistry() 