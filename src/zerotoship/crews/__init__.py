"""
Dynamic Crew Registry for tractionbuild.
Discovers and loads all crew classes automatically for plugin-style architecture.
"""

import importlib
import pkgutil
from pathlib import Path
import logging
from typing import Dict, Type

logger = logging.getLogger(__name__)


def load_crew_registry():
    """
    Dynamically discovers and loads all '...Crew' classes from modules
    within this directory into a central registry.
    """
    registry = {}
    # Path to the current package ('crews')
    package_path = str(Path(__file__).parent)
    
    for module_info in pkgutil.iter_modules([package_path]):
        module_name = module_info.name
        try:
            # Dynamically import the module
            module = importlib.import_module(f"tractionbuild.crews.{module_name}")
            for attr_name in dir(module):
                # Look for classes ending in 'Crew'
                if attr_name.endswith("Crew") and attr_name != "Crew":  # Exclude base Crew class
                    crew_class = getattr(module, attr_name)
                    if isinstance(crew_class, type):  # Ensure it's a class
                        logger.info(f"Discovered and registered crew: {attr_name}")
                        registry[attr_name] = crew_class
        except ImportError as e:
            logger.error(f"Failed to import module {module_name}: {e}")
            
    return registry


# Load the registry once on startup
CREW_REGISTRY = load_crew_registry()

# Ensure ObservabilityCrew is available
try:
    from .observability_crew import ObservabilityCrew
    CREW_REGISTRY['ObservabilityCrew'] = ObservabilityCrew
    logger.info("ObservabilityCrew registered successfully")
except ImportError as e:
    logger.warning(f"ObservabilityCrew not available: {e}") 