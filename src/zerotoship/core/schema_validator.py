import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

def validate_and_enrich_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and enrich project data."""
    # Add validation logic here
    if not data.get('id'):
        raise ValueError("Project data missing 'id' field")
    
    if not data.get('idea'):
        raise ValueError("Project data missing 'idea' field")
    
    # Add metadata if missing
    if 'metadata' not in data:
        data['metadata'] = {}
    
    return data

def is_valid_project_data(data: Dict[str, Any]) -> bool:
    """Check if project data is valid."""
    try:
        required_fields = ['id', 'idea', 'workflow', 'state']
        for field in required_fields:
            if field not in data:
                logger.error(f"Missing required field: {field}")
                return False
        return True
    except Exception as e:
        logger.error(f"Validation error: {e}")
        return False