"""
JSON Schema Validation for ZeroToShip.
Handles dpath access issues and ensures data integrity with comprehensive validation.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from jsonschema import validate, ValidationError, Draft7Validator
import dpath.util as dpath_get

logger = logging.getLogger(__name__)


class ProjectDataValidator:
    """JSON Schema validator for project data with comprehensive error handling."""
    
    def __init__(self):
        self.schema = self._get_project_schema()
        self.validator = Draft7Validator(self.schema)
    
    def _get_project_schema(self) -> Dict[str, Any]:
        """Get the comprehensive project data schema."""
        return {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "idea": {"type": "string"},
                "workflow": {"type": "string"},
                "state": {"type": "string"},
                "validation": {
                    "type": "object",
                    "properties": {
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1, "default": 0.0},
                        "passed": {"type": "boolean", "default": False},
                        "is_technically_feasible": {"type": "boolean", "default": False},
                        "compliance_ready": {"type": "boolean", "default": False},
                        "security_approved": {"type": "boolean", "default": False}
                    },
                    "default": {}
                },
                "graph": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "default": "pending"},
                        "generated": {"type": "boolean", "default": False},
                        "nodes": {"type": "array", "default": []},
                        "edges": {"type": "array", "default": []}
                    },
                    "default": {}
                },
                "build": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "default": "pending"},
                        "completed": {"type": "boolean", "default": False},
                        "output_path": {"type": "string", "default": ""}
                    },
                    "default": {}
                },
                "marketing": {
                    "type": "object",
                    "properties": {
                        "ready": {"type": "boolean", "default": False},
                        "status": {"type": "string", "default": "pending"},
                        "materials": {"type": "array", "default": []}
                    },
                    "default": {}
                },
                "feedback": {
                    "type": "object",
                    "properties": {
                        "approved": {"type": "boolean", "default": False},
                        "quick_approval": {"type": "boolean", "default": False},
                        "enterprise_approved": {"type": "boolean", "default": False},
                        "escalated": {"type": "boolean", "default": False},
                        "rejected": {"type": "boolean", "default": False},
                        "comments": {"type": "array", "default": []}
                    },
                    "default": {}
                },
                "testing": {
                    "type": "object",
                    "properties": {
                        "passed": {"type": "boolean", "default": False},
                        "critical_failure": {"type": "boolean", "default": False},
                        "results": {"type": "array", "default": []}
                    },
                    "default": {}
                },
                "loop_iterations": {
                    "type": "object",
                    "additionalProperties": {"type": "integer", "minimum": 0},
                    "default": {}
                },
                "execution_history": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "state": {"type": "string"},
                            "crew": {"type": "string"},
                            "attempt": {"type": "integer"},
                            "success": {"type": "boolean"},
                            "timestamp": {"type": "string"}
                        }
                    },
                    "default": []
                }
            },
            "required": ["id", "idea", "workflow", "state"],
            "additionalProperties": True
        }
    
    def validate_project_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize project data with defaults."""
        try:
            # First, validate the schema
            validate(instance=data, schema=self.schema)
            logger.debug("Project data schema validation passed")
            return data
            
        except ValidationError as e:
            logger.warning(f"Schema validation failed: {e.message}")
            return self._sanitize_project_data(data)
    
    def _sanitize_project_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize project data by adding missing fields with defaults."""
        sanitized = data.copy()
        
        # Ensure required fields exist
        if 'id' not in sanitized:
            sanitized['id'] = f"project_{hash(str(data)) % 1000000}"
        if 'idea' not in sanitized:
            sanitized['idea'] = "Unknown idea"
        if 'workflow' not in sanitized:
            sanitized['workflow'] = "default_software_build"
        if 'state' not in sanitized:
            sanitized['state'] = "START"
        
        # Ensure nested objects exist with defaults
        sanitized.setdefault('validation', {})
        sanitized.setdefault('graph', {})
        sanitized.setdefault('build', {})
        sanitized.setdefault('marketing', {})
        sanitized.setdefault('feedback', {})
        sanitized.setdefault('testing', {})
        sanitized.setdefault('loop_iterations', {})
        sanitized.setdefault('execution_history', [])
        
        # Set defaults for nested fields
        self._set_nested_defaults(sanitized, 'validation', {
            'confidence': 0.0,
            'passed': False,
            'is_technically_feasible': False,
            'compliance_ready': False,
            'security_approved': False
        })
        
        self._set_nested_defaults(sanitized, 'graph', {
            'status': 'pending',
            'generated': False,
            'nodes': [],
            'edges': []
        })
        
        self._set_nested_defaults(sanitized, 'build', {
            'status': 'pending',
            'completed': False,
            'output_path': ''
        })
        
        self._set_nested_defaults(sanitized, 'marketing', {
            'ready': False,
            'status': 'pending',
            'materials': []
        })
        
        self._set_nested_defaults(sanitized, 'feedback', {
            'approved': False,
            'quick_approval': False,
            'enterprise_approved': False,
            'escalated': False,
            'rejected': False,
            'comments': []
        })
        
        self._set_nested_defaults(sanitized, 'testing', {
            'passed': False,
            'critical_failure': False,
            'results': []
        })
        
        logger.info("Project data sanitized with defaults")
        return sanitized
    
    def _set_nested_defaults(self, data: Dict[str, Any], key: str, defaults: Dict[str, Any]) -> None:
        """Set defaults for nested object fields."""
        if key not in data:
            data[key] = {}
        
        for field, default_value in defaults.items():
            if field not in data[key]:
                data[key][field] = default_value
    
    def safe_get(self, data: Dict[str, Any], path: str, default: Any = None) -> Any:
        """Safely get a value from nested data using dpath with validation."""
        try:
            # First validate the data
            validated_data = self.validate_project_data(data)
            
            # Use dpath to get the value
            value = dpath_get.get(validated_data, path, default)
            
            logger.debug(f"Safe get '{path}' = {value}")
            return value
            
        except Exception as e:
            logger.error(f"Error getting path '{path}': {e}")
            return default
    
    def safe_set(self, data: Dict[str, Any], path: str, value: Any) -> Dict[str, Any]:
        """Safely set a value in nested data using dpath with validation."""
        try:
            # First validate the data
            validated_data = self.validate_project_data(data)
            
            # Use dpath to set the value
            dpath_get.set(validated_data, path, value)
            
            logger.debug(f"Safe set '{path}' = {value}")
            return validated_data
            
        except Exception as e:
            logger.error(f"Error setting path '{path}': {e}")
            return data
    
    def validate_condition_field(self, data: Dict[str, Any], field: str) -> bool:
        """Validate that a condition field exists and is accessible."""
        try:
            validated_data = self.validate_project_data(data)
            value = dpath_get.get(validated_data, field, None)
            return value is not None
        except Exception as e:
            logger.error(f"Error validating condition field '{field}': {e}")
            return False
    
    def get_validation_errors(self, data: Dict[str, Any]) -> List[str]:
        """Get all validation errors for project data."""
        errors = []
        
        try:
            self.validator.validate(data)
        except ValidationError as e:
            for error in self.validator.iter_errors(data):
                errors.append(f"{error.path}: {error.message}")
        
        return errors


# Global validator instance
PROJECT_VALIDATOR = ProjectDataValidator() 