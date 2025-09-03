"""
Robust schema validation for tractionbuild workflows.
Enforces configuration integrity and prevents runtime errors from malformed YAML.
"""

import logging
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from jsonschema import validate, ValidationError

logger = logging.getLogger(__name__)

# Schema for a single, standard step
STANDARD_STEP_SCHEMA = {
    "type": "object",
    "properties": {
        "state": {"type": "string"},
        "crew": {"type": "string"},
        "conditions": {"type": "array"},
        "timeout": {"type": "integer"},
        "retry_attempts": {"type": "integer"}
    },
    "required": ["state", "crew"]
}

# Schema for parallel step
PARALLEL_STEP_SCHEMA = {
    "type": "object",
    "properties": {
        "parallel": {
            "type": "array",
            "items": STANDARD_STEP_SCHEMA,
            "minItems": 1
        },
        "conditions": {"type": "array"}
    },
    "required": ["parallel"]
}

# Schema for loop step
LOOP_STEP_SCHEMA = {
    "type": "object",
    "properties": {
        "loop": {
            "type": "object",
            "properties": {
                "state_prefix": {"type": "string"},
                "crew": {"type": "string"},
                "max_iterations": {"type": "integer"},
                "break_conditions": {"type": "array"},
                "sequence": {
                    "type": "array",
                    "items": STANDARD_STEP_SCHEMA
                }
            },
            "required": ["state_prefix", "crew", "max_iterations"]
        }
    },
    "required": ["loop"]
}

# Schema for terminal state
TERMINAL_STEP_SCHEMA = {
    "type": "object",
    "properties": {
        "state": {"enum": ["COMPLETED", "ERROR"]}
    },
    "required": ["state"]
}

# Comprehensive schema for the entire workflow file
WORKFLOW_SCHEMA = {
    "type": "object",
    "patternProperties": {
        ".*": {  # Apply to each workflow definition
            "type": "object",
            "properties": {
                "metadata": {
                    "type": "object",
                    "properties": {
                        "compliance": {"type": "array", "items": {"type": "string"}},
                        "audit": {"type": "boolean"},
                        "visualize": {"type": "boolean"},
                        "description": {"type": "string"},
                        "estimated_duration": {"type": "string"},
                        "complexity": {"type": "string"},
                        "encryption_enabled": {"type": "boolean"},
                        "ml_optimization": {"type": "boolean"}
                    }
                },
                "sequence": {
                    "type": "array",
                    "items": {
                        # Each item in the sequence must be ONE of these valid structures
                        "oneOf": [
                            STANDARD_STEP_SCHEMA,
                            PARALLEL_STEP_SCHEMA,
                            LOOP_STEP_SCHEMA,
                            TERMINAL_STEP_SCHEMA
                        ]
                    },
                    "minItems": 1
                }
            },
            "required": ["sequence"]
        }
    },
    "minProperties": 1
}


def validate_workflows_against_schema(workflows: Dict[str, Any]) -> bool:
    """
    Validates the entire workflows.yaml content against the master schema.
    
    Args:
        workflows: The loaded workflow configuration
        
    Returns:
        True if valid, raises ValueError if invalid
        
    Raises:
        ValueError: If the workflow configuration is invalid
    """
    try:
        validate(instance=workflows, schema=WORKFLOW_SCHEMA)
        logger.info("✅ Workflow configuration schema validated successfully.")
        return True
    except ValidationError as e:
        error_path = '/'.join(map(str, e.path)) if e.path else 'root'
        logger.error(f"❌ Invalid structure in workflows.yaml: {e.message} at path '{error_path}'")
        logger.error(f"   Context: {e.context}")
        # Fail fast: an invalid config should halt the system before it starts.
        raise ValueError(f"Workflow configuration is invalid at path '{error_path}': {e.message}") from e


def validate_single_workflow(workflow_name: str, workflow: Dict[str, Any]) -> bool:
    """
    Validates a single workflow against the schema.
    
    Args:
        workflow_name: Name of the workflow being validated
        workflow: The workflow configuration
        
    Returns:
        True if valid, raises ValueError if invalid
    """
    try:
        # Create a temporary workflows dict with just this workflow
        temp_workflows = {workflow_name: workflow}
        validate(instance=temp_workflows, schema=WORKFLOW_SCHEMA)
        logger.info(f"✅ Workflow '{workflow_name}' schema validated successfully.")
        return True
    except ValidationError as e:
        error_path = '/'.join(map(str, e.path)) if e.path else 'root'
        logger.error(f"❌ Invalid structure in workflow '{workflow_name}': {e.message} at path '{error_path}'")
        raise ValueError(f"Workflow '{workflow_name}' configuration is invalid at path '{error_path}': {e.message}") from e


def validate_step_definition(step: Dict[str, Any], step_index: int) -> bool:
    """
    Validates a single step definition.
    
    Args:
        step: The step definition to validate
        step_index: Index of the step in the sequence
        
    Returns:
        True if valid, raises ValueError if invalid
    """
    try:
        # Determine which schema to use based on step structure
        if 'state' in step and 'crew' in step:
            schema = STANDARD_STEP_SCHEMA
        elif 'parallel' in step:
            schema = PARALLEL_STEP_SCHEMA
        elif 'loop' in step:
            schema = LOOP_STEP_SCHEMA
        elif 'state' in step and step['state'] in ['COMPLETED', 'ERROR']:
            schema = TERMINAL_STEP_SCHEMA
        else:
            raise ValueError(f"Step {step_index} has unrecognized structure: {step}")
        
        validate(instance=step, schema=schema)
        logger.debug(f"✅ Step {step_index} schema validated successfully.")
        return True
    except ValidationError as e:
        error_path = '/'.join(map(str, e.path)) if e.path else 'root'
        logger.error(f"❌ Invalid structure in step {step_index}: {e.message} at path '{error_path}'")
        raise ValueError(f"Step {step_index} configuration is invalid at path '{error_path}': {e.message}") from e


def safe_get_nested(data: Dict[str, Any], path: str, default: Any = None) -> Any:
    """
    Safely get a nested value from a dictionary using dot notation.
    
    Args:
        data: The dictionary to search
        path: Dot-separated path (e.g., 'validation.confidence')
        default: Default value if path not found
        
    Returns:
        The value at the path, or default if not found
    """
    try:
        keys = path.split('.')
        value = data
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    except (KeyError, TypeError, AttributeError):
        return default


def safe_set_nested(data: Dict[str, Any], path: str, value: Any) -> bool:
    """
    Safely set a nested value in a dictionary using dot notation.
    
    Args:
        data: The dictionary to modify
        path: Dot-separated path (e.g., 'validation.confidence')
        value: Value to set
        
    Returns:
        True if successful, False otherwise
    """
    try:
        keys = path.split('.')
        current = data
        
        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set the final value
        current[keys[-1]] = value
        return True
    except (KeyError, TypeError, AttributeError):
        return False


def validate_and_enrich_data(project_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and enrich project data with required fields.
    
    Args:
        project_data: The project data to validate and enrich
        
    Returns:
        Enriched project data
    """
    # Ensure required fields exist with defaults
    if 'id' not in project_data:
        import uuid
        project_data['id'] = f"project_{uuid.uuid4().hex[:8]}"
    
    if 'idea' not in project_data:
        project_data['idea'] = "Unknown idea"
    
    if 'workflow' not in project_data:
        project_data['workflow'] = "default_software_build"
    
    # CRITICAL: Handle state field with fallback
    if 'state' not in project_data or not project_data['state']:
        # Try to get initial state from workflow
        try:
            workflow_name = project_data.get('workflow', 'default_software_build')
            workflow_path = Path("config/workflows.yaml")
            
            if workflow_path.exists():
                with open(workflow_path, 'r') as f:
                    workflows = yaml.safe_load(f)
                
                if workflow_name in workflows:
                    sequence = workflows[workflow_name].get('sequence', [])
                    if sequence and len(sequence) > 0:
                        first_step = sequence[0]
                        if 'state' in first_step:
                            project_data['state'] = first_step['state']
                        elif 'parallel' in first_step:
                            project_data['state'] = first_step['parallel'][0]['state']
                        elif 'loop' in first_step:
                            project_data['state'] = f"{first_step['loop']['state_prefix']}_1"
                        else:
                            project_data['state'] = "IDEA_VALIDATION"
                    else:
                        project_data['state'] = "IDEA_VALIDATION"
                else:
                    project_data['state'] = "IDEA_VALIDATION"
            else:
                project_data['state'] = "IDEA_VALIDATION"
        except Exception as e:
            logger.warning(f"Could not determine initial state from workflow: {e}")
            project_data['state'] = "IDEA_VALIDATION"
    
    # Add default metadata if not present
    if 'metadata' not in project_data:
        project_data['metadata'] = {}
    
    # Add execution history if not present
    if 'execution_history' not in project_data:
        project_data['execution_history'] = []
    
    # Add state history if not present
    if 'state_history' not in project_data:
        project_data['state_history'] = []
    
    # Add created_at if not present
    if 'created_at' not in project_data:
        from datetime import datetime
        project_data['created_at'] = datetime.now().isoformat()
    
    return project_data


def is_valid_project_data(project_data: Dict[str, Any]) -> bool:
    """
    Check if project data has the required structure.
    
    Args:
        project_data: The project data to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        required_fields = ['id', 'idea', 'workflow', 'state']
        return all(field in project_data for field in required_fields)
    except Exception:
        return False 